# Local LLM Serving

Extend orcx to serve local models with optimized runtimes, pulling directly from HuggingFace.

## Motivation

orcx currently routes prompts to remote APIs via litellm. Adding local serving creates a unified tool for all LLM interactions:

| Current           | Proposed             |
| ----------------- | -------------------- |
| Remote APIs only  | Remote + Local       |
| Pay per token     | Free local inference |
| Internet required | Offline capable      |
| litellm routing   | litellm + MLX/vLLM   |

## Goals

1. **Optimal backends** - MLX on Mac, vLLM on Linux/CUDA (auto-detected)
2. **HuggingFace native** - Pull models directly from HF, no custom formats
3. **Model registry** - Map friendly names to platform-specific HF model IDs
4. **OpenAI-compatible API** - Same interface as remote providers
5. **Simple** - `orcx serve qwen3-coder` just works

## Non-Goals

- Custom model formats (use HF directly)
- Training/fine-tuning
- Multi-GPU tensor parallelism (single GPU focus)
- Kubernetes/cloud deployment
- GUI (CLI only, desktop app is separate project)

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Harness   │────▶│    orcx     │────▶│  Providers  │
│             │     │    CLI      │     │ (litellm)   │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
                    ┌─────┴─────┐
                    │   serve   │
                    │  command  │
                    └─────┬─────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
        ┌─────────┐ ┌─────────┐ ┌─────────┐
        │   MLX   │ │  vLLM   │ │ llama   │
        │ (macOS) │ │ (Linux) │ │  .cpp   │
        └─────────┘ └─────────┘ └─────────┘
```

## Commands

### `orcx serve`

Start local model server.

```bash
# Start with friendly name (auto-selects HF model for platform)
orcx serve qwen3-coder

# Start with explicit HF model
orcx serve mlx-community/Qwen3-Coder-Next-4bit

# Options
orcx serve qwen3-coder --port 8080
orcx serve qwen3-coder --host 0.0.0.0
orcx serve qwen3-coder --context-length 32768

# Stop server
orcx serve --stop

# Status
orcx serve --status
```

### `orcx pull`

Download model from HuggingFace.

```bash
# Pull by friendly name (resolves to platform-specific model)
orcx pull qwen3-coder

# Pull explicit HF model
orcx pull mlx-community/Qwen3-Coder-Next-4bit

# List downloaded models
orcx pull --list

# Remove model
orcx pull --remove qwen3-coder
```

### `orcx models`

List available models.

```bash
orcx models              # All models (remote aliases + local)
orcx models --local      # Local models only
orcx models --remote     # Remote aliases only
orcx models --available  # Registry models available to pull
```

### Updated `orcx run`

Route to local server when running.

```bash
# Use local model (if server running)
orcx run -m local/qwen3-coder "hello"

# Or configure default to use local
orcx run "hello"  # routes to local if configured
```

## Model Registry

Map friendly names to platform-specific HF models.

### `~/.config/orcx/models.yaml`

```yaml
models:
  qwen3-coder:
    description: "Qwen3 Coder Next (80B/3B MoE) - Best coding model"
    mlx: mlx-community/Qwen3-Coder-Next-4bit
    vllm: QuantTrio/Qwen3-Coder-Next-AWQ
    context: 131072

  glm-4.7-flash:
    description: "GLM 4.7 Flash - Fast general purpose"
    mlx: mlx-community/GLM-4.7-Flash-4bit
    vllm: cyankiwi/GLM-4.7-Flash-AWQ-4bit
    context: 131072

  deepseek-r1:
    description: "DeepSeek R1 - Reasoning model"
    mlx: mlx-community/DeepSeek-R1-0528-Qwen3-8B-4bit
    vllm: deepseek-ai/DeepSeek-R1-0528-Qwen3-8B
    context: 65536

  llama-3.3:
    description: "Llama 3.3 70B - Meta's flagship"
    mlx: mlx-community/Llama-3.3-70B-Instruct-4bit
    vllm: hugging-quants/Meta-Llama-3.3-70B-Instruct-AWQ-INT4
    context: 131072
```

### Built-in Registry

Ship with curated list of ~20 popular models. User can override/extend in config.

## Backend Detection

```python
def get_backend() -> Backend:
    """Auto-detect optimal backend for current platform."""
    if sys.platform == "darwin":
        # Check for Apple Silicon
        if platform.machine() == "arm64":
            return MLXBackend()
        raise UnsupportedPlatform("Intel Mac not supported")

    if sys.platform == "linux":
        # Check for CUDA
        if shutil.which("nvidia-smi"):
            return VLLMBackend()
        # Fallback to llama.cpp for CPU
        return LlamaCppBackend()

    raise UnsupportedPlatform(f"Unsupported: {sys.platform}")
```

## Backend Interface

```python
from abc import ABC, abstractmethod

class Backend(ABC):
    @abstractmethod
    def install_deps(self) -> None:
        """Install backend dependencies if needed."""

    @abstractmethod
    def pull(self, model_id: str) -> Path:
        """Download model, return cache path."""

    @abstractmethod
    def serve(self, model_id: str, port: int, **kwargs) -> Process:
        """Start server, return process handle."""

    @abstractmethod
    def stop(self) -> None:
        """Stop running server."""

    @abstractmethod
    def status(self) -> ServerStatus:
        """Get server status."""
```

## MLX Backend

```python
class MLXBackend(Backend):
    def install_deps(self):
        # Install mlx-lm if not present
        subprocess.run([
            "uv", "pip", "install", "--python", sys.executable, "mlx-lm"
        ])

    def serve(self, model_id: str, port: int, **kwargs):
        return subprocess.Popen([
            sys.executable, "-m", "mlx_lm", "server",
            "--model", model_id,
            "--port", str(port),
        ])
```

## vLLM Backend

```python
class VLLMBackend(Backend):
    def install_deps(self):
        subprocess.run([
            "uv", "pip", "install", "--system", "vllm",
            "--pre", "--extra-index-url", "https://wheels.vllm.ai/nightly"
        ])

    def serve(self, model_id: str, port: int, **kwargs):
        cmd = [
            "vllm", "serve", model_id,
            "--host", "0.0.0.0",
            "--port", str(port),
            "--gpu-memory-utilization", "0.90",
        ]
        if "awq" in model_id.lower():
            cmd.extend(["--quantization", "awq"])
        return subprocess.Popen(cmd)
```

## Configuration

### Extended `~/.config/orcx/config.yaml`

```yaml
# Existing config...
default_model: openrouter/deepseek/deepseek-v3.2

# New local serving config
local:
  # Default model for `orcx serve` with no args
  default_model: qwen3-coder

  # Server settings
  port: 8080
  host: localhost

  # Auto-start server when using local model
  auto_serve: false

  # Backend override (default: auto-detect)
  # backend: mlx | vllm | llamacpp
```

## Integration with Existing Features

### Conversations

Local model conversations work the same as remote:

```bash
orcx serve qwen3-coder
orcx run -m local/qwen3-coder "explain decorators"
# [a1b2]
orcx -c "show example"  # continues conversation
```

### Cost Tracking

Local models show $0.00 cost but track token usage:

```bash
orcx run -m local/qwen3-coder "hello" --cost
# ...response...
# Tokens: 150 in, 50 out | Cost: $0.00 (local)
```

### Agents

Agents can specify local models:

```yaml
agents:
  local-coder:
    model: local/qwen3-coder
    system_prompt: You are a coding assistant.
```

## File Structure

```
src/orcx/
├── cli.py              # Add serve, pull commands
├── config.py           # Add local config section
├── router.py           # Add local:// routing
├── serve/
│   ├── __init__.py
│   ├── backend.py      # Backend ABC
│   ├── mlx.py          # MLX backend
│   ├── vllm.py         # vLLM backend
│   ├── llamacpp.py     # llama.cpp fallback
│   ├── registry.py     # Model name → HF ID mapping
│   └── manager.py      # Server lifecycle management
└── ...existing...
```

## Dependencies

New optional dependencies:

```toml
[project.optional-dependencies]
serve = [
    "huggingface_hub>=0.27.0",
]

# Platform-specific (installed by backend)
# mlx-lm (Mac)
# vllm (Linux/CUDA)
# llama-cpp-python (fallback)
```

## Implementation Phases

### Phase 1: Core Serving

- [ ] Backend detection and interface
- [ ] MLX backend implementation
- [ ] vLLM backend implementation
- [ ] `orcx serve` command
- [ ] Server lifecycle (start/stop/status)

### Phase 2: Model Management

- [ ] Model registry (YAML)
- [ ] Built-in model list (~20 models)
- [ ] `orcx pull` command
- [ ] `orcx models` command
- [ ] HuggingFace cache integration

### Phase 3: Integration

- [ ] `local://` routing in router.py
- [ ] Agent support for local models
- [ ] Conversation support
- [ ] Token/cost tracking for local

### Phase 4: Polish

- [ ] llama.cpp fallback backend
- [ ] Auto-serve option
- [ ] Context length configuration
- [ ] Error handling and recovery
- [ ] Documentation

## Testing

```bash
# Unit tests
pytest tests/serve/

# Integration tests (require hardware)
pytest tests/serve/integration/ -m mlx      # Mac only
pytest tests/serve/integration/ -m vllm     # Linux/CUDA only
```

## Open Questions

1. **Daemon mode?** - Run server as background daemon vs foreground process
2. **Multiple models?** - Support serving multiple models simultaneously?
3. **Health checks?** - Automatic restart on crash?
4. **Remote serving?** - Expose to network (security considerations)?

## References

- [mlx-lm](https://github.com/ml-explore/mlx-lm) - MLX language model inference
- [vLLM](https://github.com/vllm-project/vllm) - High-throughput LLM serving
- [huggingface_hub](https://github.com/huggingface/huggingface_hub) - HF model downloads
- [litellm](https://github.com/BerriAI/litellm) - Existing provider routing
