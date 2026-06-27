import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Ingestion from './pages/Ingestion';
import Training from './pages/Training';
import Evaluation from './pages/Evaluation';
import Settings from './pages/Settings';
import { useAuth } from './contexts/AuthContext';

function App() {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="App">
      <header className="app-header">
        <h1>LBOS-AI Control Panel</h1>
        <div className="user-info">
          Welcome, {user?.username || 'User'}!
        </div>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/ingestion" element={<Ingestion />} />
          <Route path="/training" element={<Training />} />
          <Route path="/evaluation" element={<Evaluation />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;