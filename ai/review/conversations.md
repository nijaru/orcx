# Conversations Feature Review

**Date:** 2026-01-06
**Files Reviewed:**

- `src/orcx/conversation.py`
- `src/orcx/cli.py`
- `src/orcx/router.py`
- `src/orcx/schema.py`
- `tests/test_conversation.py`

## Verification Results

| Check      | Status  |
| ---------- | ------- |
| Build      | PASS    |
| Lint       | PASS    |
| Type check | PASS    |
| Tests      | 53 pass |

## Bugs

### 1. `clean()` Function Never Deletes Anything (HIGH)

**Location:** `src/orcx/conversation.py:176-184`

The `clean()` function's SQL comparison always evaluates false due to string format mismatch:

```python
def clean(days: int = 30) -> int:
    cutoff = datetime.now(UTC).isoformat()
    with _connect() as conn:
        cursor = conn.execute(
            "DELETE FROM conversations WHERE updated_at < datetime(?, ?)",
            (cutoff, f"-{days} days"),
        )
    return cursor.rowcount
```

**Problem:** ISO format stored in DB (`2026-01-07T05:34:31+00:00`) uses 'T' separator. SQLite `datetime()` returns space separator (`2026-01-07 05:34:31`). String comparison fails because 'T' (ASCII 84) > ' ' (ASCII 32), so `updated_at < computed_cutoff` is always false.

**Test confirmation:**

```python
>>> conversation.create(model='test/model')
>>> conversation.clean(0)  # Should delete everything
0  # Deleted nothing
>>> conversation.list_recent()
[...]  # Still has the conversation
```

**Fix:** Replace ISO format with SQLite-compatible format, or use `strftime('%Y-%m-%d %H:%M:%S', 'now')` directly in SQL.

### 2. ID Collision Not Handled (MEDIUM)

**Location:** `src/orcx/conversation.py:50-80`

`create()` generates a random ID without collision retry. If collision occurs, raw `sqlite3.IntegrityError` propagates.

**Impact:** With 4-char base36 IDs (1,679,616 possible), collision probability becomes significant at ~1,000 conversations (birthday paradox).

**Fix:** Retry loop with new ID on IntegrityError.

### 3. Race Condition on Update (LOW)

**Location:** `src/orcx/conversation.py:123-144`

`update()` performs read-modify-write without locking. Concurrent updates lose messages.

**Test:** 5 threads x 10 updates = 50 expected messages, only 10 saved.

**Impact:** Low for CLI usage (single user), but would break any parallel usage.

## Spec Deviations

Comparing implementation to `ai/design/conversations.md`:

| Aspect       | Spec                                | Implementation |
| ------------ | ----------------------------------- | -------------- |
| ID length    | 6 characters                        | 4 characters   |
| Message.role | `Literal["user","assistant","sys"]` | `str` (any)    |
| Message      | Has `timestamp` field               | No timestamp   |

**Impact:** ID length affects collision probability (36^4 vs 36^6). Role validation allows invalid roles through.

## Missing Test Coverage

| Scenario                   | Status  |
| -------------------------- | ------- |
| `clean()` functionality    | MISSING |
| ID collision handling      | MISSING |
| Concurrent access          | MISSING |
| CLI `--continue` flag      | MISSING |
| CLI `--resume` flag        | MISSING |
| CLI `--no-save` flag       | MISSING |
| Integration with router    | MISSING |
| Large conversation storage | MISSING |

Current tests cover CRUD basics but not edge cases or CLI integration.

## Code Quality

### Good Patterns

- Parameterized SQL queries (SQL injection safe)
- Pydantic models for serialization
- Context manager for DB connections
- Index on `updated_at` for list performance

### Issues

**1. Repeated `Conversation` construction:**

```python
# This pattern appears 4 times in conversation.py:
Conversation(
    id=row["id"],
    model=row["model"],
    agent=row["agent"],
    title=row["title"],
    messages=[Message(**m) for m in json.loads(row["messages"])],
    total_tokens=row["total_tokens"],
    total_cost=row["total_cost"],
    created_at=row["created_at"],
    updated_at=row["updated_at"],
)
```

Should extract to `_row_to_conversation(row)` helper.

**2. Connection per operation:**

```python
with _connect() as conn:  # Opens new connection every time
```

For typical CLI usage this is fine, but wasteful if doing multiple operations.

**3. Mutable default in `_save_conversation`:**

```python
def _save_conversation(conv, request, prompt, response_content, response, conversation):
```

The `conversation` parameter shadows the module import, making the signature confusing.

## Security

| Aspect           | Status |
| ---------------- | ------ |
| SQL injection    | Safe   |
| Path traversal   | N/A    |
| Secrets in DB    | Safe   |
| File permissions | N/A    |

DB is created with default permissions in user config dir. No sensitive data beyond prompts/responses.

## Recommendations

### Must Fix (Bugs)

1. **Fix `clean()` SQL** - Use consistent datetime format
2. **Handle ID collisions** - Retry loop or increase ID length to spec's 6 chars

### Should Fix (Quality)

3. Extract `_row_to_conversation()` helper
4. Add `Literal` constraint to `Message.role`
5. Add missing test coverage for `clean()` and CLI flags

### Consider

6. Increase ID length to 6 per spec
7. Add `timestamp` to `Message` per spec (may be intentional simplification)
