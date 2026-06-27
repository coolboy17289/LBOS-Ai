import React, { useEffect, useState } from 'react';
import { 
  Grid, 
  Card, 
  CardContent, 
  Typography, 
  Button, 
  TextField, 
  CircularProgress, 
  Divider, 
  Container 
} from '@mui/material';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [recentActivity, setRecentActivity] = useState<any[]>([]);
  const [modelUsage, setModelUsage] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Fetch stats
        const statsResponse = await fetch('/api/stats');
        const statsData = await statsResponse.json();
        setStats(statsData);
        
        // Fetch recent activity
        const activityResponse = await fetch('/api/activity/recent');
        const activityData = await activityResponse.json();
        setRecentActivity(activityData);
        
        // Fetch model usage stats
        const usageResponse = await fetch('/api/models/usage');
        const usageData = await usageResponse.json();
        setModelUsage(usageData);
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
        setError('Failed to load dashboard data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  if (isLoading) {
    return (
      <Grid container sx={{ pt: 4 }}>
        <Grid item xs={12}>
          <Typography align="center" variant="h4">
            Loading Dashboard...
          </Typography>
          <CircularProgress />
        </Grid>
      </Grid>
    );
  }

  if (error) {
    return (
      <Grid container sx={{ pt: 4 }}>
        <Grid item xs={12}>
          <Typography color="error" align="center">
            Error loading dashboard: {error}
          </Typography>
        </Grid>
      </Grid>
    );
  }

  return (
    <Container sx={{ pt: 4 }}>
      <Typography variant="h4" align="center" mb={4}>
        LBOS-AI Dashboard
      </Typography>

      {/* System Overview Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="text.primary">
                System Status
              </Typography>
              <Typography variant="h2">
                {stats?.status === 'online' ? 'Online' : 'Offline'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="text.primary">
                Models Loaded
              </Typography>
              <Typography variant="h2">
                {stats?.modelsLoaded || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="text.primary">
                Total Requests
              </Typography>
              <Typography variant="h2">
                {stats?.totalRequests || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="text.primary">
                Avg Response Time
              </Typography>
              <Typography variant="h2">
                {stats?.avgResponseTime?.toFixed(1) || 0}ms
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Model Usage Section */}
      <Grid item xs={12} mb={4}>
        <Card>
          <CardContent>
            <Typography variant="h5" gutterBottom>
              Model Usage Statistics
            </Typography>
            {modelUsage.length > 0 ? (
              <Grid container spacing={3}>
                {modelUsage.map((model: any) => (
                  <Grid item xs={12} sm={6} md={4} key={model.name}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" color="text.primary">
                          {model.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Type: {model.type}
                        </Typography>
                        <Divider />
                        <Typography variant="body1">
                          Requests: {model.requestCount}
                        </Typography>
                        <Typography variant="body1">
                          Avg. Response Time: {model.avgResponseTime?.toFixed(1) || 0}ms
                        </Typography>
                        <Typography variant="body1">
                          Success Rate: {(model.successRate * 100).toFixed(1)}%
                        </Typography>
                      </CardContent>
                    </Card>
                  >
                ))}
              </Grid>
            ) : (
              <Typography align="center" color="text.secondary">
                No model usage data available
              </Typography>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Recent Activity */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h5" gutterBottom>
              Recent Activity
            </Typography>
            {recentActivity.length > 0 ? (
              <div>
                {recentActivity.map((activity: any, index: number) => (
                  <div key={index} sx={{ mb: 2, p: 2, borderRadius: 1, bgcolor: 'grey.50' }}>
                    <Typography variant="body2" fontWeight="medium">
                      {activity.type}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {activity.description}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(activity.timestamp).toLocaleString()}
                    </Typography>
                    {activity.modelUsed && (
                      <Typography variant="caption" color="primary">
                        Model: {activity.modelUsed}
                      </Typography>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <Typography align="center" color="text.secondary">
                No recent activity
              </Typography>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Container>
  );
};

export default Dashboard;
