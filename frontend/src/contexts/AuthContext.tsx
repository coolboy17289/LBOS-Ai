import React, { createContext, useContext, useState, useEffect } from 'react';

interface AuthContextType {
  user: {
    id: number;
    username: string;
    email?: string;
    role: string;
  } | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<{
    id: number;
    username: string;
    email?: string;
    role: string;
  } | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check if user is already logged in (e.g., from localStorage)
    const storedUser = localStorage.getItem('lbos_user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
      setIsAuthenticated(true);
    }
  }, []);

  const login = async (username: string, password: string) => {
    // In a real app, this would call your authentication API
    // For demo purposes, we'll simulate a successful login
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Mock user data
      const mockUser = {
        id: 1,
        username: username,
        email: `${username}@example.com`,
        role: 'admin'
      };

      setUser(mockUser);
      setIsAuthenticated(true);
      localStorage.setItem('lbos_user', JSON.stringify(mockUser));
    } catch (error) {
      throw new Error('Invalid credentials');
    }
  };

  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
    localStorage.removeItem('lbos_user');
    window.location.href = '/login';
  };

  if (typeof AuthContext === 'undefined') {
    throw new Error('AuthProvider must be used within AuthProvider');
  }

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};