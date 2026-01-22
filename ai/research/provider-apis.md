# Provider API Configuration Research

Research on LLM provider APIs and what configuration options each supports beyond standard model parameters.

## Summary

| Provider      | Category   | Notable Config Options                                                     |
| ------------- | ---------- | -------------------------------------------------------------------------- |
| OpenRouter    | Aggregator | Full provider routing, quantization, performance thresholds, cost controls |
| OpenAI        | Direct     | Organization/project IDs, custom base URLs                                 |
| Anthropic     | Direct     | Service tiers, regions (via partners), beta headers                        |
| Google/Gemini | Direct     | Safety settings, regions                                                   |
| Mistral       | Direct     | Minimal - mostly standard params                                           |
| Together AI   | Inference  | Dedicated endpoints, hardware selection, regions                           |
| Fireworks AI  | Inference  | Direct routing, regions, hardware tiers                                    |
| Groq          | Inference  | Service tiers, rate limits vary by plan                                    |

---

## 1. OpenRouter (Aggregator)

OpenRouter is the only true aggregator with comprehensive provider routing. All options passed via `provider` object in request body.

### Provider Routing Options

| Field                      | Type          | Default   | Description                                                      |
| -------------------------- | ------------- | --------- | ---------------------------------------------------------------- |
| `order`                    | string[]      | -         | Provider slugs to try in order (e.g., `["anthropic", "openai"]`) |
| `allow_fallbacks`          | boolean       | `true`    | Allow backup providers when primary unavailable                  |
| `require_parameters`       | boolean       | `false`   | Only use providers supporting all request params                 |
| `data_collection`          | string        | `"allow"` | `"allow"` or `"deny"` for data collection                        |
| `zdr`                      | boolean       | -         | Restrict to Zero Data Retention endpoints                        |
| `enforce_distillable_text` | boolean       | -         | Restrict to models allowing text distillation                    |
| `only`                     | string[]      | -         | Whitelist - only allow these providers                           |
| `ignore`                   | string[]      | -         | Blacklist - skip these providers                                 |
| `quantizations`            | string[]      | -         | Filter by quantization (e.g., `["fp8", "fp16"]`)                 |
| `sort`                     | string/object | -         | Sort: `"price"`, `"throughput"`, `"latency"`                     |
| `max_price`                | object        | -         | Max pricing: `{"prompt": 1, "completion": 2}` ($/M tokens)       |
| `preferred_min_throughput` | number/object | -         | Min throughput threshold (tokens/sec)                            |
| `preferred_max_latency`    | number/object | -         | Max latency threshold (ms)                                       |

### Quantization Levels

| Level  | Description                   |
| ------ | ----------------------------- |
| `int4` | Integer (4 bit)               |
| `int8` | Integer (8 bit)               |
| `fp4`  | Floating point (4 bit)        |
| `fp6`  | Floating point (6 bit)        |
| `fp8`  | Floating point (8 bit)        |
| `fp16` | Floating point (16 bit)       |
| `bf16` | Brain floating point (16 bit) |
| `fp32` | Floating point (32 bit)       |

### Performance Thresholds

Percentile-based thresholds (p50, p75, p90, p99) over rolling 5-minute window:

```python
{
    "preferred_min_throughput": {"p90": 50},  # 50 tokens/sec at p90
    "preferred_max_latency": {"p90": 2000}    # 2 seconds at p90
}
```

### Advanced Sorting

When using model fallbacks, `sort` can specify cross-model sorting:

```python
{
    "sort": {
        "by": "throughput",  # "price", "throughput", "latency"
        "partition": "none"  # "model" (default) or "none" (global sort)
    }
}
```

### Rate Limits

- Account-level, not per-key
- Free tier: 20 RPM, 50/day (<$10 credits) or 1000/day (>=$10 credits)
- Model-specific limits vary
- Check via `GET /api/v1/key`

### Provider-Specific Headers

OpenRouter passes through certain provider headers, e.g., Anthropic beta features.

---

## 2. OpenAI (Direct Provider)

### Authentication & Organization

| Header/Param          | Description                       |
| --------------------- | --------------------------------- |
| `Authorization`       | Bearer token (API key)            |
| `OpenAI-Organization` | Organization ID for billing/usage |
| `OpenAI-Project`      | Project ID for scoping            |

### Custom Endpoints

- `base_url` can be set to custom endpoint (e.g., Azure, proxy)
- Organization/project IDs route usage tracking

### Rate Limit Headers (Response)

| Header                           | Description                     |
| -------------------------------- | ------------------------------- |
| `x-ratelimit-limit-requests`     | Max requests in window          |
| `x-ratelimit-limit-tokens`       | Max tokens in window            |
| `x-ratelimit-remaining-requests` | Remaining requests              |
| `x-ratelimit-remaining-tokens`   | Remaining tokens                |
| `x-ratelimit-reset-requests`     | Time until request limit resets |
| `x-ratelimit-reset-tokens`       | Time until token limit resets   |

### Debug Headers (Response)

| Header                 | Description                   |
| ---------------------- | ----------------------------- |
| `openai-organization`  | Organization for this request |
| `openai-processing-ms` | Processing time               |
| `x-request-id`         | Unique request identifier     |

### Custom Request ID

Pass `X-Client-Request-Id` header for your own trace ID (useful for debugging).

---

## 3. Anthropic (Direct Provider)

### Authentication

| Header              | Required | Description                      |
| ------------------- | -------- | -------------------------------- |
| `x-api-key`         | Yes      | API key from Console             |
| `anthropic-version` | Yes      | API version (e.g., `2023-06-01`) |
| `content-type`      | Yes      | `application/json`               |

### Beta Features

Use `anthropic-beta` header to access preview features. See [beta headers docs](https://docs.anthropic.com/en/api/beta-headers).

### Service Tiers

- **Standard**: Default usage tier
- **Priority Tier**: Enhanced service levels with committed spend

### Regions & Cloud Partners

Anthropic direct API is global. Regional control available via:

- **Amazon Bedrock**: Cross-region inference
- **Google Vertex AI**: Global endpoint, regional deployments
- **Azure AI**: Regional deployments

### Rate Limits

Organized into usage tiers that increase automatically:

- Spend limits (monthly)
- RPM (requests per minute)
- TPM (tokens per minute)

---

## 4. Google Gemini (Direct Provider)

### Safety Settings

Five adjustable categories with threshold controls:

| Category          | HarmCategory Enum                 |
| ----------------- | --------------------------------- |
| Harassment        | `HARM_CATEGORY_HARASSMENT`        |
| Hate Speech       | `HARM_CATEGORY_HATE_SPEECH`       |
| Sexually Explicit | `HARM_CATEGORY_SEXUALLY_EXPLICIT` |
| Dangerous Content | `HARM_CATEGORY_DANGEROUS_CONTENT` |
| Civic Integrity   | (election-related queries)        |

### Block Thresholds

| Setting    | API Value                | Description                           |
| ---------- | ------------------------ | ------------------------------------- |
| Off        | `OFF`                    | Turn off safety filter                |
| Block none | `BLOCK_NONE`             | Always show regardless of probability |
| Block few  | `BLOCK_ONLY_HIGH`        | Block high probability only           |
| Block some | `BLOCK_MEDIUM_AND_ABOVE` | Block medium or high (default)        |
| Block most | `BLOCK_LOW_AND_ABOVE`    | Block low, medium, or high            |

### Usage Example

```python
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
]
```

### Regions

Available in multiple regions - see [available regions](https://ai.google.dev/gemini-api/docs/available-regions).

---

## 5. Mistral AI (Direct Provider)

### Configuration

Mistral offers minimal provider-specific configuration:

- Standard completion parameters
- API key authentication
- No special routing or region options

### Features

- Chat completions
- Embeddings
- Function calling
- Structured outputs
- Moderation/guardrailing
- Fine-tuning
- Batch inference

---

## 6. Together AI (Inference Platform)

### Serverless vs Dedicated

| Mode       | Description                              |
| ---------- | ---------------------------------------- |
| Serverless | Shared infrastructure, pay-per-token     |
| Dedicated  | Custom endpoints with hardware selection |

### Dedicated Endpoint Options

| Option                | Description                         |
| --------------------- | ----------------------------------- |
| `--gpu`               | Hardware type (a100, h100)          |
| `--gpu-count`         | GPUs per replica (2, 4, 8)          |
| `--min-replicas`      | Minimum replicas (default: 1)       |
| `--max-replicas`      | Maximum replicas (auto-scales)      |
| `--inactive-timeout`  | Auto-shutdown after inactivity      |
| `--availability-zone` | Specific zone (e.g., us-central-4b) |

### Features

| Feature              | Flag                               |
| -------------------- | ---------------------------------- |
| Speculative decoding | Remove `--no-speculative-decoding` |
| Prompt caching       | Remove `--no-prompt-cache`         |

### Hardware Options

- NVIDIA A100 (80GB)
- NVIDIA H100 (80GB)

### Rate Limits

Apply at organization level, not per-user.

---

## 7. Fireworks AI (Inference Platform)

### Deployment Modes

| Mode                    | Description                              |
| ----------------------- | ---------------------------------------- |
| Serverless              | Global load balancer                     |
| Direct Routing          | Bypasses load balancer for lower latency |
| Private Service Connect | GCP PSC                                  |
| AWS PrivateLink         | AWS private networking                   |

### Direct Routing Regions

| Region            | Hardware   |
| ----------------- | ---------- |
| `US_IOWA_1`       | H100 80GB  |
| `US_VIRGINIA_1`   | H100 80GB  |
| `US_ARIZONA_1`    | H100 80GB  |
| `US_ILLINOIS_1`   | H100 80GB  |
| `US_TEXAS_1`      | H100 80GB  |
| `US_CALIFORNIA_1` | H200 141GB |
| `US_GEORGIA_2`    | B200 180GB |
| `EU_FRANKFURT_1`  | H100 80GB  |
| `EU_ICELAND_1`    | H200 141GB |
| `AP_TOKYO_1`      | H100 80GB  |

### Direct Route Usage

```python
# OpenAI SDK - include /v1
client = OpenAI(base_url="https://...direct.fireworks.ai/v1")

# Fireworks SDK - omit /v1
client = Fireworks(base_url="https://...direct.fireworks.ai")
```

### Features

- Zero Data Retention (ZDR)
- Custom model uploads
- Quantization options
- LoRA fine-tuning

---

## 8. Groq (Inference Platform)

### Rate Limit Metrics

| Metric | Description            |
| ------ | ---------------------- |
| RPM    | Requests per minute    |
| RPD    | Requests per day       |
| TPM    | Tokens per minute      |
| TPD    | Tokens per day         |
| ASH    | Audio seconds per hour |
| ASD    | Audio seconds per day  |

### Service Tiers

| Tier        | Description                          |
| ----------- | ------------------------------------ |
| Free        | Limited rates, basic access          |
| Developer   | Higher limits, batch/flex processing |
| Performance | Enhanced service levels              |
| Enterprise  | Dedicated/multi-tenant instances     |

### Rate Limit Headers (Response)

| Header                           | Description                       |
| -------------------------------- | --------------------------------- |
| `retry-after`                    | Seconds until retry (only on 429) |
| `x-ratelimit-limit-requests`     | RPD limit                         |
| `x-ratelimit-limit-tokens`       | TPM limit                         |
| `x-ratelimit-remaining-requests` | Remaining RPD                     |
| `x-ratelimit-remaining-tokens`   | Remaining TPM                     |

### Special Features

- Prompt caching (cached tokens don't count toward limits)
- Flex processing (lower cost, flexible timing)
- Batch processing

---

## Cross-Provider Settings (via litellm)

litellm provides unified configuration that applies to any provider.

### Timeout Configuration

| Setting           | Scope        | Description                           |
| ----------------- | ------------ | ------------------------------------- |
| `timeout`         | Global/Model | Max time for complete response        |
| `stream_timeout`  | Model        | Max time for first chunk in streaming |
| `request_timeout` | Global       | Default: 6000s                        |

### Retry Configuration

| Setting                | Description                    |
| ---------------------- | ------------------------------ |
| `num_retries`          | Number of retries (default: 3) |
| `retry_policy`         | Retries per exception type     |
| `allowed_fails`        | Failures before cooldown       |
| `allowed_fails_policy` | Failures by error type         |

### Fallback Configuration

| Setting                    | Description                          |
| -------------------------- | ------------------------------------ |
| `fallbacks`                | Model fallback chains (all errors)   |
| `context_window_fallbacks` | Fallback on context exceeded         |
| `content_policy_fallbacks` | Fallback on content policy violation |
| `default_fallbacks`        | Default if model group fails         |
| `max_fallbacks`            | Max fallback attempts (default: 5)   |

### Routing Strategies

| Strategy                | Description                      |
| ----------------------- | -------------------------------- |
| `simple-shuffle`        | Random selection (default)       |
| `least-busy`            | Route to least loaded deployment |
| `usage-based-routing`   | Route based on TPM/RPM           |
| `latency-based-routing` | Route to lowest latency          |

### Pre-Call Checks

| Setting                 | Description                      |
| ----------------------- | -------------------------------- |
| `enable_pre_call_check` | Check context window before call |
| `region_name`           | Filter by deployment region      |

### Rate Limit Handling

| Setting             | Description                      |
| ------------------- | -------------------------------- |
| `rpm`               | Requests per minute limit        |
| `tpm`               | Tokens per minute limit          |
| `cooldown_time`     | Cooldown duration after failures |
| `disable_cooldowns` | Disable cooldown behavior        |

### Provider-Specific via `extra_body`

```python
litellm.completion(
    model="openrouter/anthropic/claude-3",
    messages=[...],
    extra_body={"provider": {"quantizations": ["fp8"]}}
)
```

---

## Recommendations for orcx

### What to Expose

1. **OpenRouter-specific** (already done):
   - Quantization preferences
   - Provider filtering (ignore/only/order)
   - Sort strategy

2. **Cross-provider** (via litellm):
   - Timeout (global + per-model)
   - Retry count
   - Fallback chains

3. **Consider adding**:
   - Gemini safety settings
   - OpenRouter max_price
   - OpenRouter performance thresholds

### Config Structure

```yaml
# Global defaults
defaults:
  timeout: 120
  num_retries: 3

# Provider-specific (OpenRouter)
provider_prefs:
  quantizations: ["fp8", "fp16"]
  ignore: ["azure"]
  sort: price
  max_price:
    prompt: 1
    completion: 2

# Agent-level overrides
agents:
  fast-coder:
    model: openrouter/deepseek/deepseek-coder
    timeout: 30
    provider_prefs:
      sort: latency

  safe-assistant:
    model: gemini/gemini-pro
    safety_settings:
      harassment: BLOCK_MEDIUM_AND_ABOVE
      hate_speech: BLOCK_MEDIUM_AND_ABOVE
```

---

## Sources

- OpenRouter Provider Routing: https://openrouter.ai/docs/features/provider-routing
- OpenRouter Rate Limits: https://openrouter.ai/docs/api/reference/limits
- OpenAI API Reference: https://platform.openai.com/docs/api-reference/introduction
- Anthropic API Overview: https://docs.anthropic.com/en/api/overview
- Gemini Safety Settings: https://ai.google.dev/gemini-api/docs/safety-settings
- Mistral Docs: https://docs.mistral.ai/
- Together AI Dedicated: https://docs.together.ai/docs/dedicated-inference
- Fireworks AI Direct Routing: https://docs.fireworks.ai/deployments/direct-routing
- Fireworks AI Regions: https://docs.fireworks.ai/deployments/regions
- Groq Rate Limits: https://console.groq.com/docs/rate-limits
- litellm Fallbacks: https://docs.litellm.ai/docs/proxy/reliability
- litellm Timeouts: https://docs.litellm.ai/docs/proxy/timeout
- litellm All Settings: https://docs.litellm.ai/docs/proxy/config_settings

---

**Updated:** 2026-01-09
