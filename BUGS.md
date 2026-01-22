# orcx Bugs

## API Key Error Messages

When API keys are missing, the error messages could be more helpful:

```
Error: Missing or invalid API key for deepseek. Set DEEPSEEK_API_KEY environment variable.
Error: Missing or invalid API key for anthropic. Set ANTHROPIC_API_KEY environment variable.
```

These are fine, but it would be useful to:

1. Show which env vars ARE configured (masked)
2. Suggest `orcx models` to see available providers

## Rate Limiting

```
Error: Rate limited by openrouter
```

Could include:

- Suggested wait time
- Alternative models to try

## Model Format Errors

```
Error: Invalid model format: 'deepseek'. Expected 'provider/model-name'
```

This is clear, but could suggest the actual model name based on provider prefix (e.g., `deepseek` -> `deepseek/deepseek-chat`).

## LiteLLM Provider Error

```
Error: litellm.BadRequestError: LLM Provider NOT provided. Pass in the LLM provider...
```

This happens with `google/gemini-2.0-flash`. Either:

1. Document which providers require what format
2. Auto-map common patterns (google/\* should work)
