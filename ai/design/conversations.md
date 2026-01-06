# Conversation Management Design

## Overview

Multi-turn conversation support for orcx. Follows UX patterns from tk/jb (short IDs), llm (conversation flags), and gh (subcommand structure).

## ID Scheme

| Aspect     | Value                             |
| ---------- | --------------------------------- |
| Format     | `{prefix}-{ref}` e.g. `orcx-a1b2` |
| Ref length | 4 chars (base36, lowercase)       |
| Prefix     | Derived from agent name or `chat` |
| Uniqueness | Per data directory                |
| Collision  | Regenerate on conflict            |

Prefix examples: `chat-x9y8` (no agent), `coder-a1b2` (agent=coder)

## Storage

| Aspect   | Value                                |
| -------- | ------------------------------------ |
| Location | `~/.local/share/orcx/conversations/` |
| Format   | JSON (one file per conversation)     |
| Filename | `{id}.json`                          |
| Index    | None (glob + mtime for listing)      |

## Data Model

```python
class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime

class Conversation(BaseModel):
    id: str                           # e.g. "chat-a1b2"
    agent: str | None = None          # agent used (if any)
    model: str                        # model used
    messages: list[Message] = []
    created_at: datetime
    updated_at: datetime

    # Tracking (optional, accumulated)
    total_tokens: int = 0
    total_cost: float = 0.0

    # Metadata
    title: str | None = None          # optional user label
    tags: list[str] = []
```

## CLI Interface

### Primary Command (run)

```bash
# New conversation (default)
orcx run "prompt"

# Continue last conversation
orcx run -c "follow up"

# Continue specific conversation
orcx run -c a1b2 "follow up"
orcx run --cid chat-a1b2 "follow up"

# With agent
orcx run -a coder "prompt"
orcx run -a coder -c "follow up"   # continues last coder conv
```

### Conversation Subcommand

```bash
orcx conv                    # alias: orcx c
orcx conv list               # list all (default if no subcommand)
orcx conv list -n 10         # limit count
orcx conv list -a coder      # filter by agent
orcx conv show a1b2          # show full conversation
orcx conv show -l            # show last conversation
orcx conv delete a1b2        # delete specific
orcx conv clean              # remove old (default: 7d)
orcx conv clean --older 30d  # custom retention
orcx conv export a1b2        # JSON to stdout
orcx conv title a1b2 "name"  # set title
```

### Flag Summary

| Flag         | Short | Description                        |
| ------------ | ----- | ---------------------------------- |
| `--continue` | `-c`  | Continue conversation (last or ID) |
| `--cid`      |       | Continue by full ID                |
| `--new`      | `-n`  | Force new conversation             |
| `--agent`    | `-a`  | Agent to use                       |
| `--model`    | `-m`  | Model override                     |
| `--no-save`  |       | Don't persist this exchange        |

## Resolution Logic

```
-c         -> continue last conversation (global or agent-scoped if -a)
-c <ref>   -> find conversation by ref suffix match
--cid <id> -> exact ID match
(neither)  -> new conversation
```

Conversation scope:

- `orcx run -c "x"` continues last global conversation
- `orcx run -a coder -c "x"` continues last conversation with agent=coder

## Output Modes

| Mode      | Flag          | Description                 |
| --------- | ------------- | --------------------------- |
| Stream    | (default)     | Stream response as received |
| No stream | `--no-stream` | Wait for complete response  |
| JSON      | `--json`      | Output OrcxResponse as JSON |
| Quiet     | `-q`          | Response only, no status    |

## Lifecycle

| Action     | Trigger                                     |
| ---------- | ------------------------------------------- |
| Create     | First message with no -c flag               |
| Update     | Any -c continuation                         |
| Auto-title | Generate from first user message (truncate) |
| Delete     | `orcx conv delete` or `clean`               |
| Cleanup    | `orcx conv clean --older 7d`                |

## Conversation Listing Format

```
$ orcx conv list
ID          AGENT   MSGS  UPDATED      TITLE
chat-a1b2   -       4     2m ago       code review request
coder-x9y8  coder   12    1h ago       api design
chat-p3q4   -       2     3d ago       -
```

## Edge Cases

| Case                 | Behavior                              |
| -------------------- | ------------------------------------- |
| -c with no history   | Error: "No conversation to continue"  |
| -c ref ambiguous     | Error: "Multiple matches: X, Y"       |
| -c ref not found     | Error: "Conversation not found: ref"  |
| Agent mismatch on -c | Warning, use existing agent config    |
| Model change on -c   | Allowed (store new model in metadata) |

## Implementation Files

| File            | Purpose                             |
| --------------- | ----------------------------------- |
| schema.py       | Add Message, Conversation models    |
| conversation.py | CRUD operations, ID generation      |
| cli.py          | Add -c flag to run, conv subcommand |

## Open Questions

1. **System prompt handling**: Store with conversation or re-apply from agent config each turn?
   - Recommendation: Re-apply from agent config (simpler, allows updates)

2. **Max context management**: Truncate old messages or error?
   - Recommendation: Warn when approaching limit, let user decide

3. **Concurrent access**: Lock files or last-write-wins?
   - Recommendation: Last-write-wins (CLI tool, unlikely concurrent)
