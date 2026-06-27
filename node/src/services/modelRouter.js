/**
 * Model Router Service
 * Intelligently routes requests to appropriate models based on task complexity
 */
const axios = require('axios');
const { v4: uuidv4 } = require('uuid');
const logger = require('../utils/logger');

class ModelRouter {
  constructor() {
    this.models = {
      // Local lightweight models (Python-based)
      small: {
        endpoint: process.env.LOCAL_MODEL_URL || 'http://localhost:5001',
        type: 'local',
        maxTokens: 512,
        bestFor: ['simple_classification', 'entity_extraction', 'basic_summarization']
      },

      // Gemma 4B via llama.cpp
      medium: {
        endpoint: process.env.GEMMA_4B_URL || 'http://localhost:8080',
        type: 'llama_cpp',
        maxTokens: 2048,
        bestFor: ['general_conversation', 'complex_summarization', 'code_generation', 'reasoning']
      },

      // Reserved for future large models
      large: {
        endpoint: process.env.LARGE_MODEL_URL || '',
        type: 'external_api',
        maxTokens: 4096,
        bestFor: ['advanced_reasoning', 'creative_writing', 'complex_analysis']
      }
    };

    // Routing rules based on task characteristics
    this.routingRules = [
      {
        // Simple classification/tasks
        condition: (request) => {
          const { taskType, inputLength, complexity } = request;
          return taskType === 'classification' &&
                 inputLength < 100 &&
                 complexity === 'low';
        },
        model: 'small',
        priority: 1
      },

      // Entity extraction
      {
        condition: (request) => {
          return request.taskType === 'entity_extraction' ||
                 request.taskType === 'ner';
        },
        model: 'small',
        priority: 1
      },

      // Default to Gemma 4B for most tasks
      {
        condition: (request) => {
          return true; // Default fallback
        },
        model: 'medium',
        priority: 2
      }
    ];
  }

  /**
   * Determine the best model for a given request
   * @param {Object} request - The incoming request
   * @returns {Object} Selected model configuration
   */
  selectModel(request) {
    // Sort rules by priority (lower number = higher priority)
    const sortedRules = [...this.routingRules].sort((a, b) => a.priority - b.priority);

    for (const rule of sortedRules) {
      if (rule.condition(request)) {
        const modelKey = rule.model;
        const model = this.models[modelKey];

        logger.info(`Selected ${modelKey} model for request ${request.id || 'unknown'}`, {
          reason: `Matched rule: ${JSON.stringify(rule.condition)}`,
          requestId: request.id || 'unknown'
        });

        return { ...model, key: modelKey };
      }
    }

    // Fallback to medium model
    logger.warn('No matching rule found, falling back to medium model', {
      requestId: request.id || 'unknown'
    });
    return { ...this.models.medium, key: 'medium' };
  }

  /**
   * Forward request to selected model
   * @param {Object} request - Original request
   * @param {Object} model - Selected model configuration
   * @returns {Promise<Object>} Model response
   */
  async routeRequest(request, model) {
    const requestId = request.id || uuidv4();
    const startTime = Date.now();

    try {
      // Prepare request for target model
      const modelRequest = this.prepareModelRequest(request, model);

      // Call the model service
      let response;
      if (model.type === 'llama_cpp' && request.stream) {
        // Handle streaming response
        response = await this.streamRequest(model.endpoint, modelRequest);
      } else {
        // Standard HTTP request
        response = await axios.post(
          `${model.endpoint}/v1/${model.type === 'local' ? 'generate' : 'completions'}`,
          modelRequest,
          {
            timeout: model.timeout || 30000,
            headers: {
              'Content-Type': 'application/json',
              ...(model.headers || {})
            }
          }
        );
      }

      const responseTime = Date.now() - startTime;

      // Process and enrich response
      const processedResponse = this.processModelResponse(response.data, {
        originalRequest: request,
        modelUsed: model.key,
        responseTime,
        requestId
      });

      logger.info(`Request processed successfully`, {
        requestId,
        modelUsed: model.key,
        responseTime: `${responseTime}ms`,
        tokensGenerated: processedResponse.usage?.completion_tokens || 0
      });

      return processedResponse;
    } catch (error) {
      const responseTime = Date.now() - startTime;
      logger.error(`Error routing request to ${model.key} model`, {
        requestId,
        modelUsed: model.key,
        error: error.message,
        responseTime: `${responseTime}ms`,
        stack: error.stack
      });

      // Try fallback model if available
      if (model.key !== 'small') {
        logger.info(`Attempting fallback to small model`, { requestId });
        return this.routeRequest(request, { ...this.models.small, key: 'small' });
      }

      throw error;
    }
  }

  /**
   * Prepare request for specific model type
   * @param {Object} request - Original request
   * @param {Object} model - Target model configuration
   * @returns {Object} Formatted request for model
   */
  prepareModelRequest(request, model) {
    const baseRequest = {
      ...request,
      max_tokens: Math.min(request.max_tokens || 100, model.maxTokens)
    };

    switch (model.type) {
      case 'llama_cpp':
        return {
          model: "gemma-4b-it",
          prompt: request.prompt || request.input || "",
          max_tokens: baseRequest.max_tokens,
          temperature: request.temperature || 0.7,
          top_p: request.top_p || 0.9,
          stream: request.stream || false,
          stop: request.stop || ["</s>", "\n\n"],
          ...(request.stream && { stream: true })
        };

      case 'local':
        return {
          inputs: request.inputs || request.prompt || "",
          parameters: {
            max_new_tokens: baseRequest.max_tokens,
            temperature: request.temperature || 0.7,
            top_p: request.top_p || 0.9,
            return_full_text: false
          },
          options: {
            use_cache: false
          }
        };

      default:
        return baseRequest;
    }
  }

  /**
   * Handle streaming requests
   * @param {string} endpoint - Model endpoint URL
   * @param {Object} request - Request data
   * @returns {Promise<AsyncIterable>} Stream of response chunks
   */
  async* streamRequest(endpoint, request) {
    // In a real implementation, this would use actual streaming
    // For now, we'll simulate by making a regular request and yielding chunks
    const response = await axios.post(`${endpoint}/v1/completions`, request, {
      responseType: 'stream'
    });

    let buffer = '';
    for await (const chunk of response.data) {
      buffer += chunk.toString();
      const lines = buffer.split('\n');
      buffer = lines.pop(); // Keep incomplete line in buffer

      for (const line of lines) {
        if line.startsWith('data: ') {
          const data = line.substring(5);
          if data !== '[DONE]' {
            try {
              const parsed = JSON.parse(data);
              yield parsed;
            } catch (e) {
              // Skip malformed lines
            }
          }
        }
      }
    }
  }

  /**
   * Process and enrich model response
   * @param {Object} rawResponse - Raw response from model
   * @param {Object} context - Additional context
   * @returns {Object} Processed response
   */
  processModelResponse(rawResponse, context) {
    const { modelUsed, requestId, responseTime } = context;

    // Standardize response format
    const processed = {
      id: `cmpl-${uuidv4()}`,
      object: "text_completion",
      created: Math.floor(Date.now() / 1000),
      model: modelUsed,
      choices: [],
      usage: {
        prompt_tokens: 0,
        completion_tokens: 0,
        total_tokens: 0
      },
      metadata: {
        modelUsed,
        responseTimeMs: responseTime,
        requestId
      }
    };

    // Handle different response formats
    if (modelUsed === 'small') {
      // Local model response format
      if (Array.isArray(rawResponse) && rawResponse.length > 0) {
        const result = rawResponse[0];
        processed.choices = [{
          text: result.generated_text || '',
          index: 0,
          logprobs: null,
          finish_reason: "stop"
        }];

        // Estimate token usage
        const promptWords = (context.originalRequest.prompt || '').split(' ').length;
        const completionWords = (result.generated_text || '').split(' ').length;
        processed.usage.prompt_tokens = Math.round(promptWords * 1.3);
        processed.usage.completion_tokens = Math.round(completionWords * 1.3);
        processed.usage.total_tokens = processed.usage.prompt_tokens + processed.usage.completion_tokens;
      }
    } else {
      // llama.cpp / OpenAI format response
      if (rawResponse.choices && Array.isArray(rawResponse.choices)) {
        processed.choices = rawResponse.choices.map(choice => ({
          text: choice.text || choice.message?.content || '',
          index: choice.index || 0,
          logprobs: choice.logprobs,
          finish_reason: choice.finish_reason || "stop"
        }));

        if (rawResponse.usage) {
          processed.usage = {
            prompt_tokens: rawResponse.usage.prompt_tokens || 0,
            completion_tokens: rawResponse.usage.completion_tokens || 0,
            total_tokens: rawResponse.usage.total_tokens || 0
          };
        }
      }
    }

    return processed;
  }

  /**
   * Get model health status
   * @returns {Promise<Object>} Health status of all models
   */
  async getHealthStatus() {
    const healthPromises = Object.entries(this.models).map(async ([key, model]) => {
      try {
        if (model.type === 'local' || model.type === 'llama_cpp') {
          const response = await axios.get(`${model.endpoint}/v1/models`, {
            timeout: 5000
          });
          return { [key]: { status: 'healthy', responseTime: 0 } };
        }
        return { [key]: { status: 'unknown', reason: 'Health check not implemented' } };
      } catch (error) {
        return { [key]: { status: 'unhealthy', error: error.message } };
      }
    });

    const results = await Promise.allSettled(healthPromises);
    return Object.assign({}, ...results.map(r =>
      r.status === 'fulfilled' ? r.value : {}
    ));
  }
}

module.exports = { ModelRouter };