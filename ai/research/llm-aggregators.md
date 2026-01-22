# LLM Aggregators Research

Research on services that aggregate multiple external LLM providers (like OpenRouter) vs those that host their own infrastructure.

**Date:** 2026-01-09

## Summary

| Service                   | Type                | Aggregates External?      | Routing Options                                                     | Region/Location           | Quantization         |
| ------------------------- | ------------------- | ------------------------- | ------------------------------------------------------------------- | ------------------------- | -------------------- |
| **OpenRouter**            | Aggregator          | Yes                       | Provider order, fallbacks, quantization, latency/throughput sorting | EU residency (enterprise) | int4, int8, fp4-fp32 |
| **AWS Bedrock**           | Cloud Provider      | No (hosts on AWS)         | Cross-region inference profiles (geographic/global)                 | Yes - region profiles     | No                   |
| **Azure AI Foundry**      | Cloud Provider      | Hybrid                    | Model Router (quality/cost/balanced modes), model subset            | Data zone boundaries      | No                   |
| **Portkey**               | Gateway             | Yes (routes to external)  | Fallbacks, load balancing, geo-routing, provider selection          | Yes - geo-routing         | No                   |
| **Martian**               | Intelligent Router  | Yes                       | AI-powered query-level routing to best model                        | Implicit via providers    | No                   |
| **LiteLLM Proxy**         | Self-hosted Gateway | Yes                       | Strategies: shuffle, least-busy, latency, cost, EU-region filtering | EU region filtering       | No                   |
| **Cloudflare AI Gateway** | Gateway             | Yes (proxies to external) | Dynamic routing, fallbacks, A/B testing                             | Geographic routing        | No                   |
| **Unify**                 | Aggregator/Router   | Yes                       | Benchmark-based routing, speed/cost/quality optimization            | Implicit via providers    | No                   |

---

## Detailed Analysis

### 1. OpenRouter

**Type:** True Aggregator (routes to external providers)

**What it does:** Single API endpoint that routes requests to 20+ providers hosting the same models. You pay OpenRouter, they pay providers.

**Routing Options:**

- `order`: Specify provider priority list (e.g., `["anthropic", "openai"]`)
- `allow_fallbacks`: Enable/disable automatic fallback to other providers
- `require_parameters`: Only route to providers supporting all request parameters
- `data_collection`: Filter by provider data policies ("allow" or "deny")
- `only` / `ignore`: Whitelist or blacklist specific providers
- `sort`: Sort by price (default), throughput, or latency
- `preferred_min_throughput` / `preferred_max_latency`: Performance thresholds

**Region/Location:**

- EU data residency available for enterprise customers
- Prompts processed entirely within EU when enabled

**Quantization:**

- Filter by quantization level: `int4`, `int8`, `fp4`, `fp6`, `fp8`, `fp16`, `bf16`, `fp32`, `unknown`
- Useful for selecting model variants with different size/quality tradeoffs

**Provider-Specific Features:**

- Target specific provider endpoints (e.g., `deepinfra/turbo` vs `deepinfra`)
- Pass through provider-specific headers (e.g., `x-anthropic-beta`)

---

### 2. AWS Bedrock

**Type:** Cloud Provider (hosts models on AWS infrastructure)

**What it does:** AWS hosts foundation models from Anthropic, Meta, Mistral, Cohere, etc. on their own infrastructure. Not an aggregator - you're using AWS's capacity.

**Routing Options:**

- **Cross-Region Inference Profiles:**
  - Geographic profiles (US, EU) - routes within specific geography
  - Global profiles - routes to optimal region worldwide
- Automatic region selection based on availability and load
- Up to 2x throughput limits compared to single-region

**Region/Location:**

- Strong region control via inference profiles
- Data zone boundaries honored
- Useful for compliance (e.g., keep EU data in EU)

**Quantization:** No - models are fixed configurations

**Key Difference:** You're not routing between external providers; you're routing between AWS regions hosting the same models.

---

### 3. Azure AI Foundry (Model Router)

**Type:** Hybrid (hosts some models, routes to others like Claude)

**What it does:** Azure's Model Router is a trained language model that dynamically selects the best underlying LLM for each prompt.

**Routing Options:**

- **Routing Modes:**
  - `Balanced` (default): Considers both cost and quality
  - `Quality`: Prioritizes accuracy, ignores cost
  - `Cost`: Prioritizes savings within quality band (5-6% tolerance)
- **Model Subset:** Select which underlying models to include in routing
- Automatic routing based on prompt complexity, reasoning requirements, task type

**Supported Models (v2025-11-18):**

- OpenAI: gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, o4-mini, gpt-5, gpt-5-mini, gpt-5-nano, gpt-5-chat
- Third-party: DeepSeek-V3.1, gpt-oss-120b, Llama-4-Maverick, grok-4, grok-4-fast-reasoning
- Anthropic: claude-haiku-4-5, claude-opus-4-1, claude-sonnet-4-5 (requires separate deployment)

**Region/Location:**

- Data zone standard deployments
- Global standard deployments
- Honors data zone boundaries in routing decisions

**Quantization:** No

**Key Difference:** AI-powered routing at the prompt level - the router analyzes each prompt and picks the best model. Claude models require separate deployment before Model Router can use them.

---

### 4. Portkey

**Type:** AI Gateway (routes to external providers)

**What it does:** Open-source AI gateway that provides unified API across 100+ LLMs and 15+ providers. Routes to external providers.

**Routing Options:**

- **Fallbacks:** Automatic failover to alternative models/providers
- **Load Balancing:** Distribute requests across deployments
- **Retry Logic:** Configurable retries with exponential backoff
- **Conditional Routing:** Route based on request attributes
- **Provider Selection:** Choose which providers to use

**Region/Location:**

- **Geo-location Routing:** Route based on user's physical location
- Similar to CDN - route to nearest/most appropriate provider
- Useful for latency optimization and compliance

**Quantization:** No

**Other Features:**

- Virtual keys for API key management
- Observability and logging
- Prompt management
- Guardrails
- Self-hostable (open source)

---

### 5. Martian

**Type:** Intelligent Router (routes to external providers)

**What it does:** Uses AI/ML to analyze each query and route to the optimal LLM. Claims up to 99.7% cost reduction by using cheaper models when appropriate.

**Routing Options:**

- AI-powered per-query routing
- Automatic model selection based on:
  - Query complexity
  - Cost optimization
  - Performance requirements
- Automatic rerouting during provider outages
- Automatic new model integration

**Region/Location:** Implicit - inherits from underlying providers

**Quantization:** No

**How It Works:**

- "Model Mapping" technology analyzes prompts
- Patent-pending router technology
- Accenture investment and partnership
- RouterBench benchmark for evaluating routing quality

**Products:**

- **Martian Router:** Core routing product
- **Airlock:** Compliance automation for enterprise AI adoption
- **Model Gateway:** Side-by-side testing vs existing setup

---

### 6. LiteLLM Proxy

**Type:** Self-hosted Gateway (routes to external providers)

**What it does:** Open-source proxy server providing unified API to 100+ LLMs. Self-hosted, so you control the infrastructure.

**Routing Options:**

- **Load Balancing Strategies:**
  - `simple-shuffle` (default, recommended): Random distribution based on RPM/TPM weights
  - `least-busy`: Route to deployment with fewest active requests
  - `usage-based-routing`: Route to lowest usage (not recommended for production)
  - `latency-based`: Route to fastest responding deployment
  - `cost-based`: Route to cheapest deployment
  - Custom routing strategies supported

- **Fallbacks:** Automatic failover between model groups
- **Cooldowns:** Automatic cooldown on rate limits or high failure rates
- **Priority/Ordering:** `order` param to prioritize deployments
- **Weighted Distribution:** `weight` param for load distribution

**Region/Location:**

- **EU Region Filtering:** Pre-call checks to filter deployments outside EU
- Set `region_name` on deployments
- Automatic region inference for Vertex AI, Bedrock, IBM WatsonxAI

**Quantization:** No

**Budget Routing:**

- Provider budget limits
- Tag-based routing
- Request prioritization (beta)

---

### 7. Cloudflare AI Gateway

**Type:** Edge Gateway (proxies to external providers)

**What it does:** Edge-based gateway that sits between your app and AI providers. Adds caching, rate limiting, observability, and routing.

**Routing Options:**

- **Dynamic Routing:**
  - Visual flow-based configuration
  - User-based routing
  - Geographic routing
  - A/B testing and fractional traffic splitting
  - Context-aware routing based on request content
  - Automatic fallbacks

- **Rate Limiting:** Per-gateway or per-request limits
- **Fallbacks:** Automatic failover during provider issues

**Region/Location:**

- Geographic routing based on user location
- Edge-based - requests processed at nearest Cloudflare PoP

**Quantization:** No

**Supported Providers (20+):**
Amazon Bedrock, Anthropic, Azure OpenAI, Cohere, Google Vertex AI, Groq, HuggingFace, Mistral, OpenAI, Perplexity, Replicate, Together AI, Workers AI, and more.

**Other Features:**

- Caching (up to 90% latency reduction)
- Guardrails (content moderation)
- DLP (data loss prevention)
- BYOK (bring your own keys)
- Analytics and logging

---

### 8. Unify

**Type:** Aggregator/Router (routes to external providers)

**What it does:** Single access point to multiple LLMs with automatic routing optimization for speed, latency, and cost.

**Routing Options:**

- Automatic routing to optimal endpoint
- User-defined parameters for:
  - Cost constraints
  - Latency requirements
  - Output speed preferences
- Custom quality metrics
- Benchmark-based routing

**Region/Location:** Implicit - inherits from underlying providers

**Quantization:** No

**Key Features:**

- Transparent daily runtime and quality benchmarks (publicly accessible)
- Integration with LangChain and LlamaIndex
- Founded by PhD from Imperial College London

---

## Comparison: Aggregators vs Providers vs Gateways

### True Aggregators (route to multiple external providers)

- **OpenRouter**: Most comprehensive provider/routing options
- **Unify**: Benchmark-driven routing optimization

### Intelligent Routers (AI-powered model selection)

- **Martian**: Per-query AI routing, patent-pending technology
- **Azure Model Router**: Prompt-analyzed routing within Azure ecosystem

### Self-hosted Gateways

- **LiteLLM Proxy**: Full control, extensive routing strategies
- **Portkey**: Open source, enterprise features

### Edge Gateways

- **Cloudflare AI Gateway**: Edge caching, visual routing, DLP

### Cloud Providers (host their own)

- **AWS Bedrock**: Cross-region inference, not true aggregation
- **Azure AI**: Hybrid - hosts some, routes to others (Claude)

---

## Recommendations for orcx

Given orcx uses LiteLLM, the most relevant patterns are:

1. **Provider Filtering:** OpenRouter's `only`/`ignore` pattern for provider selection
2. **Region Filtering:** LiteLLM's EU region filtering, Portkey's geo-routing
3. **Quantization:** OpenRouter's quantization filtering (unique feature)
4. **Routing Modes:** Azure's Quality/Cost/Balanced paradigm
5. **Performance Thresholds:** OpenRouter's latency/throughput preferences

### Key Insight

OpenRouter is the only service offering:

- Direct quantization filtering
- Provider-specific endpoint targeting (e.g., `deepinfra/turbo`)
- Comprehensive performance sorting with thresholds

This makes OpenRouter the most feature-rich for routing control when using external providers. For self-hosted scenarios, LiteLLM Proxy provides similar capabilities.

---

## Sources

- OpenRouter Docs: https://openrouter.ai/docs/guides/routing/provider-selection
- AWS Bedrock Cross-Region: https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html
- Azure Model Router: https://learn.microsoft.com/en-us/azure/ai-foundry/openai/concepts/model-router
- Portkey Docs: https://docs.portkey.ai/
- Martian: https://withmartian.com/
- LiteLLM Routing: https://docs.litellm.ai/docs/routing
- Cloudflare AI Gateway: https://developers.cloudflare.com/ai-gateway/
- Unify: https://unify.ai/
