import React, { useState, useEffect } from 'react';
import { Grid, Card, CardContent, Typography, Button, CircularProgress, Tooltip } from '@mui/material';
import { UseCase } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const { data: stats, loading, error } = useApi('/api/stats');
  const [recentJobs, setRecentJobs] = useState<any[]>([]);

  useEffect(() => {
    // Fetch recent jobs
    fetch('/api/jobs?limit=5')
      .then(res => res.json())
      .then(data => setRecentJobs(data.jobs || []))
      .catch(err => console.error('Failed to fetch recent jobs:', err));
  }, []);

  if (loading) {
    return (
      <Grid container spacing={2}>
        <Grid item xs={12}>
          <Typography variant="h4" align="center">
            Loading Dashboard...
          </Typography>
          <CircularProgress />
        </Grid>
      </Grid>
    );
  }

  if (error) {
    return (
      <Grid container spacing={2}>
        <Grid item xs={12}>
          <Typography color="error" align="center">
            Error loading dashboard: {error}
          </Typography>
        </Grid>
      </Grid>
    );
  }

  return (
    <>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* System Status Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="text.secondary">
                System Status
              </Typography>
              <Typography variant="h4">
                {stats?.status || 'Online'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="text.secondary">
                Models Trained
              </Typography>
              <Typography variant="h4">
                {stats?.models || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="text.secondary">
                Datasets Processed
              </Typography>
              <Typography variant="h4">
                {stats?.datasets || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="text.secondary">
                Evaluations Run
              </Typography>
              <Typography variant="h4">
                {stats?.evaluations || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Grid item xs={12} mt={4}>
        <Card>
          <CardContent>
            <Typography variant="h5" gutterBottom>
              Recent Activity
            </Typography>
            {recentJobs.length > 0 ? (
              <div>
                {recentJobs.map((job: any) => (
                  <div key={job.jobId} sx={{ mb: 2, p: 1, borderBottom: 1, borderColor: 'divider' }}>
                    <Typography variant="body1" color="text.primary">
                      {job.type}: {job.jobId.substring(0, 8)}...
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {job.status} • {new Date(job.createdAt).toLocaleTimeString()}
                    </Typography>
                  </div>
                ))}
              </div>
            ) : (
              <Typography color="text.secondary">
                No recent activity
              </Typography>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Quick Actions */}
      <Grid item xs={12} mt={4}>
        <Card>
          <CardContent>
            <Typography variant="h5" gutterBottom>
              Quick Actions
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Button
                  variant="contained"
                  color="primary"
                  size="large"
                  fullWidth
                  startIcon={<AddCircleOutline />}
                >
                  New Ingestion
                </Button>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Button
                  variant="contained"
                  color="success"
                  size="large"
                  fullWidth
                  startIcon={<TrendingUp />}
                >
                  Start Training
                </Button>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Button
                  variant="contained"
                  color="info"
                  size="large"
                  fullWidth
                  startIcon={<BarChart />}
                >
                  Run Evaluation
                </Button>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Button
                  variant="contained"
                  color="warning"
                  size="large"
                  fullWidth
                  startIcon={<Settings />}
                >
                  Settings
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>
    </>
  );
};

export default Dashboard;