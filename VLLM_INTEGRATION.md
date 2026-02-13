# VLLM Integration with Crawl4AI

This document explains how to configure Crawl4AI to work with vllm containers, specifically for the Qwen2.5-VL-7B-Instruct model.

## Problem Analysis

The original setup had several issues:

1. **Network Isolation**: The crawl4ai container was trying to access `https://localhost:8000`, but `localhost` inside a container refers to the container itself, not the host machine.

2. **Protocol Mismatch**: The vllm container typically runs on HTTP, not HTTPS, but the configuration was using `https://`.

3. **Container Communication**: The containers were not on the same Docker network, preventing them from communicating by name.

## Solution

The solution involves three main components:

### 1. Docker Network Setup

Create a shared Docker network for both containers:

```bash
docker network create crawl4ai-network
```

### 2. Updated .llm.env Configuration

The original `.llm.env` file:
```env
VLLM_API_KEY=VLLM
VLLM_BASE_URL=https://localhost:8000
```

Should be replaced with:
```env
# VLLM Configuration for Qwen2.5-VL-7B-Instruct
LLM_PROVIDER=qwen/qwen2.5-vl-7b-instruct
LLM_BASE_URL=http://vllm-qwen2.5-vl-7b:8000/v1
VLLM_API_KEY=VLLM
```

**Key Changes:**
- `LLM_PROVIDER`: Specifies the model provider and model name
- `LLM_BASE_URL`: Uses the container name as hostname and `http://` protocol
- The `/v1` path is required for OpenAI-compatible endpoints

### 3. Updated Docker Run Commands

**vllm container:**
```bash
docker run -d --gpus all --ipc=host --name vllm-qwen2.5-vl-7b \
  --network crawl4ai-network \
  -v /home/user/.cache/huggingface:/root/.cache/huggingface \
  -p 8000:8000 \
  vllm/vllm-openai:latest \
  Qwen/Qwen2.5-VL-7B-Instruct \
  --gpu-memory-utilization 0.9 \
  --max-model-len 32768 \
  --trust-remote-code \
  --limit-mm-per-prompt  '{"image": 4}'
```

**crawl4ai container:**
```bash
docker run -d \
  -p 11235:11235 \
  --name crawl4ai \
  --network crawl4ai-network \
  --env-file .llm.env \
  --shm-size=1g \
  unclecode/crawl4ai:latest
```

## How It Works

### Container Communication

1. Both containers are placed on the `crawl4ai-network` Docker network
2. Docker's internal DNS allows containers to resolve each other by name
3. The crawl4ai container can now access the vllm container using `http://vllm-qwen2.5-vl-7b:8000/v1`

### LLM Configuration Flow

1. **Environment Variables**: The `.llm.env` file provides configuration via environment variables
2. **Config Loading**: The crawl4ai server loads these variables through `python-dotenv`
3. **LLMConfig Creation**: When LLM operations are performed, an `LLMConfig` object is created with:
   - `provider`: From `LLM_PROVIDER` environment variable
   - `base_url`: From `LLM_BASE_URL` environment variable  
   - `api_token`: From `VLLM_API_KEY` environment variable
4. **LiteLLM Integration**: The `LLMConfig` is passed to LiteLLM, which handles the actual API calls to vllm

### Provider Format

The `LLM_PROVIDER` follows the format `provider/model`:
- `qwen/qwen2.5-vl-7b-instruct` tells LiteLLM to use the Qwen provider with the specified model
- This format is consistent with other providers like `openai/gpt-4o`, `anthropic/claude-3-sonnet`, etc.

## Files Created

This solution includes several files to help with setup:

1. **vllm_setup_guide.md**: Comprehensive guide with detailed explanations
2. **.llm.env.example**: Example configuration file
3. **setup_vllm_crawl4ai.sh**: Automation script to set up everything

## Verification

To verify the setup is working:

1. **Check container connectivity:**
   ```bash
   docker exec -it crawl4ai ping vllm-qwen2.5-vl-7b
   ```

2. **Test vllm endpoint directly:**
   ```bash
   curl http://localhost:8000/v1/models
   ```

3. **Test through crawl4ai API:**
   ```bash
   curl -X POST http://localhost:11235/llm/extract \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com", "instruction": "Extract main content"}'
   ```

## Troubleshooting

### Common Issues and Solutions

**Issue: "Connection refused" or "Cannot resolve hostname"**
- **Cause**: Containers are not on the same network or using wrong hostname
- **Solution**: Ensure both containers use `--network crawl4ai-network` and use the container name as hostname

**Issue: SSL/HTTPS errors**
- **Cause**: Using `https://` instead of `http://`
- **Solution**: VLLM typically runs on HTTP, update `LLM_BASE_URL` to use `http://`

**Issue: API authentication failed**
- **Cause**: Incorrect API key or authentication issues
- **Solution**: VLLM doesn't require authentication, ensure `VLLM_API_KEY` is set (any value works)

**Issue: Model not found**
- **Cause**: Incorrect provider/model format
- **Solution**: Use the correct format `qwen/qwen2.5-vl-7b-instruct`

## Advanced Configuration

You can customize the LLM behavior with additional environment variables:

```env
# Basic configuration
LLM_PROVIDER=qwen/qwen2.5-vl-7b-instruct
LLM_BASE_URL=http://vllm-qwen2.5-vl-7b:8000/v1
VLLM_API_KEY=VLLM

# Optional parameters
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
LLM_TOP_P=0.9
LLM_FREQUENCY_PENALTY=0.0
LLM_PRESENCE_PENALTY=0.0
```

These parameters will be automatically picked up by the `LLMConfig` class and passed to LiteLLM.

## Technical Details

### Environment Variable Priority

The crawl4ai system uses the following priority for LLM configuration:

1. **Direct API parameters** (highest priority)
2. **Environment variables** (from `.llm.env` or `-e` flags)
3. **Config file settings** (`config.yml`)
4. **Default values** (lowest priority)

### LiteLLM Provider Support

Crawl4AI uses LiteLLM for provider-agnostic LLM integration. LiteLLM supports:

- OpenAI-compatible endpoints (like vllm)
- Direct provider APIs (OpenAI, Anthropic, etc.)
- Local models (Ollama, etc.)
- Custom endpoints

The vllm container provides an OpenAI-compatible endpoint at `/v1`, which LiteLLM can consume directly.

### Container Networking

Docker networks provide:
- **Isolation**: Containers on different networks cannot communicate
- **DNS Resolution**: Containers can resolve each other by name
- **Security**: Network-level security policies
- **Performance**: Optimized container-to-container communication

By placing both containers on `crawl4ai-network`, they can communicate efficiently and securely.

## Conclusion

This solution enables Crawl4AI to seamlessly integrate with vllm containers by:

1. **Proper Networking**: Using Docker networks for container communication
2. **Correct Configuration**: Using the right provider format and base URL
3. **Protocol Compatibility**: Using HTTP instead of HTTPS
4. **Environment Variables**: Leveraging the existing configuration system

The setup maintains compatibility with Crawl4AI's existing LLM integration while enabling powerful local model serving through vllm.