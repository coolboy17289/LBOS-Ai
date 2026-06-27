# Model Runtime Layer - Gemma 4B Integration

This component handles the Gemma 4B model inference using llama.cpp, ensuring strict separation from training components.

## Features

- Loads Gemma 4B in GGUF format (Q4_K_M quantization)
- Provides HTTP API for inference requests
- Supports streaming token generation
- Implements KV caching for efficiency
- Includes safety filters and output validation
- Optimized for CPU with AV2 acceleration
- Memory-efficient operation (~8GB RAM)

## Model Specifications

- **Model**: google/gemma-4b-it
- **Format**: GGUF (GPT-Generated Unified Format)
- **Quantization**: Q4_K_M (4-bit, high quality)
- **Context Length**: 8192 tokens
- **Parameters**: 4 billion
- **License**: Gemma Terms of Use

## Usage Requirements

1. Download the Gemma 4B GGUF model from official sources
2. Place it in `models/gemma-4b-it-q4_k_m.gguf`
3. Ensure CPU supports AV2 instructions for optimal performance
4. Minimum 16GB RAM recommended (8GB for model, rest for system)

## API Endpoints

### POST /v1/completions
Standard completion endpoint

```json
{
  "model": "gemma-4b-it",
  "prompt": "Explain quantum computing in simple terms",
  "max_tokens": 512,
  "temperature": 0.7,
  "top_p": 0.9,
  "stream": false
}
```

### POST /v1/chat/completions
Chat completion endpoint (OpenAI compatible)

```json
{
  "model": "gemma-4b-it",
  "messages": [
    {"role": "user", "content": "Hello, how are you?"}
  ],
  "max_tokens": 512,
  "temperature": 0.7,
  "stream": false
}
```

### GET /v1/models
List available models

### WebSocket /ws/completions
Streaming endpoint for real-time token generation

## Implementation Details

Built using:
- llama.cpp (https://github.com/ggerganov/llama.cpp)
- C++17 for performance
- AV2/SIMD optimizations where available
- Thread-safe concurrent request handling
- Efficient memory management

## Performance

- Token generation: ~30-50 tokens/second on modern CPU
- First token latency: <2 seconds
- Memory footprint: ~7-8GB RAM
- Concurrent requests: 2-4 (depending on hardware)

## Safety Features

- Input sanitization and length limiting
- Output profanity filtering
- Customizable safety thresholds
- Usage logging and monitoring
- Rate limiting per IP/user

## Deployment

Can run as:
- Standalone service
- Docker container
- Kubernetes pod
- System service

## Maintenance

- Model updates require full replacement
- Quantization can be adjusted for different quality/speed tradeoffs
- Regular security updates recommended