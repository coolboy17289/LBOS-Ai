import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  CircularProgress,
  Container
} from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const Login: React.FC = () => {
  const { login, loading } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      alert('Login failed. Please check your credentials.');
    }
  };

  if (loading) {
    return (
      <Container sx={{ py: 8 }}>
        <Typography variant="h4" align="center" mb={4}>
          LBOS-AI
        </Typography>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="xs" sx={{ py: 8 }}>
      <Typography variant="h4" align="center" mb={4}>
        LBOS-AI
      </Typography>
      <Typography variant="h6" align="center" mb={2}>
        Sign in to your account
      </Typography>

      <form onSubmit={handleSubmit} sx={{ width: '100%', mt: 3 }}>
        <TextField
          label="Email Address"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          fullWidth
          mb={2}
          autoFocus
        />
        <TextField
          label="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          fullWidth
          mb={3>
        />
        <Button
          type="submit"
          variant="contained"
          color="primary"
          fullWidth
          size="large"
        >
          Sign In
        </Button>
        <Typography
          variant="body2"
          color="text.secondary"
          align="center"
          mt={3}
        >
          Don't have an account?{" "}
          <span
            onClick={() => navigate('/register')}
            style={{ textDecoration: 'underline', cursor: 'pointer' }}
          >
            Sign up
          </span>
        </Typography>
      </form>
    </Container>
  );
};

export default Login;