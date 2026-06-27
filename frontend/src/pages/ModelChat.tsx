import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  CircularProgress,
  MenuItem,
  Select,
  InputLabel,
  FormControl,
  Stack,
  Divider,
  Chip
} from '@mui/material';
import { useApi } from '../hooks/useApi';

const ModelChat: React.FC = () => {
  const { data: chatResponse, loading, error } = useApi('/api/chat', {
    method: 'POST',
    skip: true
  });

  const [messages, setMessages] = useState<Array<{text: string, isUser: boolean, modelUsed?: string, timestamp: string}>>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState('auto');
  const [models, setModels] = useState<Array<{value: string, label: string}>>([
    { value: 'auto', label: 'Auto Select' },
    { value: 'small', label: 'Small (Local)' },
    { value: 'medium', label: 'Medium (Gemma 4B)' },
    { value: 'large', label: 'Large (Gemma 5B)' }
  ]);

  useEffect(() => {
    // Fetch available models on load
    fetch('/api/models/available')
      .then(res => res.json())
      .then(data => {
        if (data && Array.isArray(data.models)) {
          const modelOptions = data.models.map((model: any) => ({
            value: model.id,
            label: `${model.name} (${model.size}B)`
          }));
          setModels([
            { value: 'auto', label: 'Auto Select' },
            ...modelOptions
          ]);
        }
      })
      .catch(err => console.error('Failed to fetch models:', err));
  }, []);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = {
      text: input,
      isUser: true,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          model: selectedModel === 'auto' ? undefined : selectedModel
        })
      });

      const data = await response.json();

      const botMessage = {
        text: data.response,
        isUser: false,
        modelUsed: data.modelUsed,
        timestamp: new Date().toLocaleTimeString()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      console.error('Error sending message:', err);
      setMessages(prev => [
        ...prev,
        {
          text: 'Sorry, I encountered an error. Please try again.',
          isUser: false,
          timestamp: new Date().toLocaleTimeString()
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };

  if (isLoading && messages.length === 0) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h5">Loading AI models...</Typography>
        <CircularProgress size={48} />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 4, height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ flexGrow: 1, overflowY: 'auto', pb: 4 }}>
        <Typography variant="h6" align="center" mb={4}>
          LBOS-AI Chat Interface
        </Typography>

        {/* Model Selector */}
        <FormControl sx={{ mb: 2, width: '100%' }}>
          <InputLabel id="model-select-label">Model Selection</InputLabel>
          <Select
            labelId="model-select-label"
            value={selectedModel}
            label="Model Selection"
            onChange={(e) => setSelectedModel(e.target.value as string)}
            sx={{ width: '100%' }}
          >
            {models.map(option => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <Divider sx={{ my: 2 }} />

        {/* Chat Messages */}
        {messages.map((msg, index) => (
          <Box
            key={index}
            sx={{
              display: 'flex',
              mb: 2,
              p: 2,
              borderRadius: 2,
              bgcolor: msg.isUser ? 'primary.main' : 'grey.200',
              justifyContent: msg.isUser ? 'flex-end' : 'flex-start'
            }}
          >
            <Box
              sx={{
                maxWidth: '80%',
                color: msg.isUser ? 'white' : 'text.primary'
              }}
            >
              <Typography variant="body1" sx={{ mb: 1 }}>
                {msg.text}
              </Typography>
              {msg.modelUsed && (
                <Typography variant="caption" sx={{ opacity: 0.8 }}>
                  Model: {msg.modelUsed.toUpperCase()}
                </Typography>
              )}
              <Typography variant="caption" sx={{ opacity: 0.6, textAlign: 'right' }}>
                {msg.timestamp}
              </Typography>
            </Box>
          </Box>
        ))}
      </Box>

      <Box sx={{ pt: 2, borderTop: '1px solid', borderColor: 'grey.300' }}>
        <Stack direction="row" spacing={2} sx={{ width: '100%' }}>
          <TextField
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type a message..."
            sx={{ flexGrow: 1 }}
            disabled={isLoading}
          />
          <Button
            variant="contained"
            color="primary"
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            sx={{ px: 4 }}
          >
            {isLoading ? 'Sending...' : 'Send'}
          </Button>
        </Stack>
      </Box>
    </Box>
  );
};

export default ModelChat;
