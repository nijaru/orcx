# Bug Fix Review: Commit e16d2df

**Date:** 2026-01-06
**Commit:** e16d2df - Fix conversation bugs found in review

## Verification Results

| Check      | Status  |
| ---------- | ------- |
| Build      | PASS    |
| Lint       | PASS    |
| Type check | PASS    |
| Tests      | 53 pass |

## Fix 1: ID Collision Retry

**Status: WORKING**

**Change:**

```python
# Before: Single insert, IntegrityError propagates
conv = Conversation(id=_generate_id(), ...)
conn.execute("INSERT ...", (...))

# After: Retry loop (10 attempts)
for _ in range(10):
    conv_id = _generate_id()
    try:
        conn.execute("INSERT ...", (...))
        return Conversation(id=conv_id, ...)
    except sqlite3.IntegrityError:
        continue
raise RuntimeError("Failed to generate unique conversation ID")
```

**Verification:**

```python
# Forced collision test
collision_count = 0
def mock_generate():
    collision_count += 1
    if collision_count <= 3:
        return "test"  # Force collision
    return original_generate()

c1 = conv.create(model='test/model')  # id='verm'
conv._generate_id = mock_generate
c2 = conv.create(model='test/model')  # Retries, gets different ID
# PASS: Different IDs generated
```

**Assessment:** Fix is correct. RuntimeError after 10 retries is appropriate.

## Fix 2: clean() datetime

**Status: STILL BROKEN**

**Change:**

```python
# Before (broken):
cutoff = datetime.now(UTC).isoformat()
cursor = conn.execute(
    "DELETE FROM conversations WHERE updated_at < datetime(?, ?)",
    (cutoff, f"-{days} days"),
)

# After (still broken):
cursor = conn.execute(
    "DELETE FROM conversations WHERE updated_at < datetime('now', ?)",
    (f"-{days} days",),
)
```

**Verification:**

```python
>>> c = conv.create(model='test/model')
>>> conv.list_recent()
[Conversation(id='tnye', ...)]
>>> conv.clean(0)  # Should delete everything
0  # Deleted nothing
>>> conv.list_recent()
[Conversation(id='tnye', ...)]  # Still there
# FAIL: clean() does not delete anything
```

**Root Cause:**

The timestamps stored in DB use ISO format from `_now()`:

```
2026-01-07T05:49:31.284240+00:00
```

SQLite `datetime('now', '-N days')` returns:

```
2026-01-07 05:49:31
```

String comparison: `'T' (ASCII 84) > ' ' (ASCII 32)`, so `updated_at < cutoff` is always false.

**Correct Fix Options:**

1. **Change storage format** - Make `_now()` return SQLite-compatible format:

   ```python
   def _now() -> str:
       return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
   ```

2. **Use strftime in SQL** - Normalize stored value:

   ```python
   cursor = conn.execute(
       "DELETE FROM conversations WHERE strftime('%Y-%m-%d %H:%M:%S', updated_at) < datetime('now', ?)",
       (f"-{days} days",),
   )
   ```

3. **Use replace() in SQL** - Convert T to space:
   ```python
   cursor = conn.execute(
       "DELETE FROM conversations WHERE replace(updated_at, 'T', ' ') < datetime('now', ?)",
       (f"-{days} days",),
   )
   ```

Option 1 is cleanest but requires migration of existing data. Option 3 works with existing data.

## Summary

| Fix              | Intended Purpose               | Status       |
| ---------------- | ------------------------------ | ------------ |
| ID collision     | Retry on IntegrityError        | WORKING      |
| clean() datetime | Use SQLite datetime comparison | STILL BROKEN |

## Recommendation

The `clean()` function needs a second fix. The simplest approach that works with existing data:

```python
def clean(days: int = 30) -> int:
    """Delete conversations older than N days. Returns count deleted."""
    with _connect() as conn:
        cursor = conn.execute(
            "DELETE FROM conversations WHERE replace(updated_at, 'T', ' ') < datetime('now', ?)",
            (f"-{days} days",),
        )
    return cursor.rowcount
```

Or normalize the timestamp format going forward and handle the timezone suffix:

```python
def clean(days: int = 30) -> int:
    with _connect() as conn:
        cursor = conn.execute(
            "DELETE FROM conversations WHERE substr(replace(updated_at, 'T', ' '), 1, 19) < datetime('now', ?)",
            (f"-{days} days",),
        )
    return cursor.rowcount
```

This handles both the 'T' separator and strips the timezone suffix (+00:00) and microseconds.
