import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button, TextField, Typography, Box, CircularProgress } from '@mui/material';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await login(username, password);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mt: 4, px: 3, py: 4 }} maxWidth="xs">
      <Typography component="h1" variant="h5" align="center" mb={4}>
        LBOS-AI Login
      </Typography>

      {error && (
        <Typography color="error" mb={2}>
          {error}
        </Typography>
      )}

      <TextField
        label="Username"
        variant="outlined"
        margin="normal"
        required
        fullWidth
        id="username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        autoFocus
        marginBottom={2}
      />

      <TextField
        label="Password"
        type="password"
        variant="outlined"
        margin="normal"
        required
        fullWidth
        id="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        marginBottom={2}
      />

      <Button
        type="submit"
        variant="contained"
        color="primary"
        fullWidth
        disabled={loading}
      >
        {loading ? 'Signing in...' : 'Sign In'}
      </Button>

      <Box mt={3}>
        <Typography align="center" size="small">
          Demo credentials: username: demo, password: demo
        </Typography>
      </Box>
    </Box>
  );
};

export default Login;