import React, { createContext, useContext, useState, useEffect } from 'react';

interface AuthContextType {
  user: any | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    // Check for existing token or user session
    const token = localStorage.getItem('token');
    if (token) {
      // In a real app, you would validate the token with your backend
      setUser({ username: 'testuser', role: 'user' });
    }
    setIsLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    // In a real app, you would make an API call to your backend
    // For now, we'll simulate a successful login
    return new Promise<void>((resolve) => {
      setTimeout(() => {
        setUser({ username, role: 'user' });
        localStorage.setItem('token', 'fake-jwt-token');
        resolve();
      }, 1000);
    });
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('token');
  };

  const value = {
    user,
    isLoading,
    login,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};