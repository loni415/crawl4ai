# VLLM Setup Guide for Crawl4AI

This guide explains how to configure Crawl4AI to use a vllm container running Qwen2.5-VL-7B-Instruct.

## Solution Overview

The issue is that the crawl4ai container cannot access `https://localhost:8000` from inside its container. You need to:

1. Create a Docker network for container communication
2. Use the container name as the hostname instead of localhost
3. Use HTTP instead of HTTPS (vllm typically runs on HTTP)
4. Configure the LLM provider correctly

## Step-by-Step Setup

### 1. Create a Docker Network

First, create a dedicated network for your containers:

```bash
docker network create crawl4ai-network
```

### 2. Run the vllm Container

Run your vllm container on the network:

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

### 3. Update your .llm.env File

Replace the contents of your `.llm.env` file with:

```env
# VLLM Configuration for Qwen2.5-VL-7B-Instruct
LLM_PROVIDER=qwen/qwen2.5-vl-7b-instruct
LLM_BASE_URL=http://vllm-qwen2.5-vl-7b:8000/v1
VLLM_API_KEY=VLLM
```

**Important notes:**
- Use `http://` instead of `https://` (vllm typically runs on HTTP)
- Use the container name `vllm-qwen2.5-vl-7b` as the hostname
- The `/v1` path is required for OpenAI-compatible endpoints
- The `VLLM_API_KEY` can be any value since vllm doesn't require authentication by default

### 4. Run the crawl4ai Container

Run your crawl4ai container on the same network:

```bash
docker run -d \
  -p 11235:11235 \
  --name crawl4ai \
  --network crawl4ai-network \
  --env-file .llm.env \
  --shm-size=1g \
  unclecode/crawl4ai:latest
```

### 5. Alternative: Using Environment Variables Directly

If you prefer not to use a `.llm.env` file, you can set the environment variables directly:

```bash
docker run -d \
  -p 11235:11235 \
  --name crawl4ai \
  --network crawl4ai-network \
  -e LLM_PROVIDER=qwen/qwen2.5-vl-7b-instruct \
  -e LLM_BASE_URL=http://vllm-qwen2.5-vl-7b:8000/v1 \
  -e VLLM_API_KEY=VLLM \
  --shm-size=1g \
  unclecode/crawl4ai:latest
```

## Configuration Details

### LLM Provider Format

The `LLM_PROVIDER` should follow the format `provider/model`. For vllm with Qwen, use:
- `qwen/qwen2.5-vl-7b-instruct`

### Base URL Format

The `LLM_BASE_URL` should point to the vllm container's OpenAI-compatible endpoint:
- `http://vllm-qwen2.5-vl-7b:8000/v1`

The `/v1` path is important as it indicates the OpenAI API version compatibility.

### API Key

VLLM doesn't require authentication by default, so you can use any value for `VLLM_API_KEY`.

## Verification

To verify the setup is working:

1. Check that both containers are running:
   ```bash
   docker ps
   ```

2. Test connectivity from the crawl4ai container to vllm:
   ```bash
   docker exec -it crawl4ai ping vllm-qwen2.5-vl-7b
   ```

3. Test the vllm endpoint directly:
   ```bash
   curl http://vllm-qwen2.5-vl-7b:8000/v1/models
   ```

## Troubleshooting

### Issue: Connection refused
- **Cause**: Containers are not on the same network
- **Solution**: Ensure both containers use `--network crawl4ai-network`

### Issue: Cannot resolve hostname
- **Cause**: Using `localhost` instead of container name
- **Solution**: Use the container name `vllm-qwen2.5-vl-7b` as hostname

### Issue: SSL/HTTPS errors
- **Cause**: Using `https://` instead of `http://`
- **Solution**: VLLM typically runs on HTTP, use `http://` in the base URL

### Issue: API authentication failed
- **Cause**: Incorrect API key format
- **Solution**: VLLM doesn't require auth, use any value like `VLLM`

## Advanced Configuration

If you need to customize the LLM configuration further, you can set additional environment variables:

```env
LLM_PROVIDER=qwen/qwen2.5-vl-7b-instruct
LLM_BASE_URL=http://vllm-qwen2.5-vl-7b:8000/v1
VLLM_API_KEY=VLLM
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
```

These will be automatically picked up by the crawl4ai system through the LiteLLM integration.