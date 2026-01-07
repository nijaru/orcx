# Conversation Management Design

**Status: Implemented**

## Overview

Multi-turn conversation support for orcx. Simple SQLite storage, continue/resume flags.

Primary use case: Claude Code delegates to orcx, iterates on responses.

## Storage

| Aspect   | Value                               |
| -------- | ----------------------------------- |
| Location | `~/.config/orcx/conversations.db`   |
| Format   | SQLite                              |
| Why      | Reliable, queryable, no file sprawl |

### Schema

```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,          -- e.g. "a1b2c3"
    model TEXT NOT NULL,
    agent TEXT,
    title TEXT,
    messages TEXT NOT NULL,       -- JSON array
    total_tokens INTEGER DEFAULT 0,
    total_cost REAL DEFAULT 0.0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_updated ON conversations(updated_at DESC);
```

## CLI Interface

### Run Command

```bash
# New conversation
orcx run -m deepseek "explain this code"

# Continue last conversation
orcx run -c "what about error handling?"

# Resume specific conversation
orcx run --resume a1b2c3 "one more question"
```

### Conversations Command

```bash
orcx conversations              # List recent
orcx conversations show a1b2c3  # Show full conversation
orcx conversations delete a1b2c3
orcx conversations clean        # Remove old (default: 30d)
```

## Flags

| Flag       | Short | Description                  |
| ---------- | ----- | ---------------------------- |
| --continue | -c    | Continue last conversation   |
| --resume   |       | Resume specific conversation |
| --no-save  |       | Don't persist this exchange  |

## Data Model

```python
class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime

class Conversation(BaseModel):
    id: str
    model: str
    agent: str | None = None
    title: str | None = None
    messages: list[Message] = []
    total_tokens: int = 0
    total_cost: float = 0.0
    created_at: datetime
    updated_at: datetime
```

## ID Generation

- 6 character base36 (lowercase alphanumeric)
- Generated on first message
- Example: `a1b2c3`, `x9y8z7`

## Implementation

| File            | Purpose                      |
| --------------- | ---------------------------- |
| conversation.py | SQLite CRUD, ID generation   |
| cli.py          | Add -c, --resume flags       |
| schema.py       | Message, Conversation models |

## Edge Cases

| Case               | Behavior                             |
| ------------------ | ------------------------------------ |
| -c with no history | Error: "No conversation to continue" |
| --resume not found | Error: "Conversation not found"      |
| Model change on -c | Allowed, use new model               |

## Not Implementing (Keep Simple)

- Conversation branching
- Agent-scoped conversations
- Complex title generation
- File export
