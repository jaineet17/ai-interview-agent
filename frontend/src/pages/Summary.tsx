import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Card,
  CardContent,
  Divider,
  Chip,
  Button,
  Rating,
  Alert,
  Stack,
  TextField,
  Grid,
  CircularProgress,
  Tab,
  Tabs,
} from '@mui/material';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import HomeIcon from '@mui/icons-material/Home';
import PrintIcon from '@mui/icons-material/Print';
import DownloadIcon from '@mui/icons-material/Download';
import BarChartIcon from '@mui/icons-material/BarChart';
import AssessmentIcon from '@mui/icons-material/Assessment';
import InterviewSummaryVisual from '../components/InterviewSummaryVisual';
import api from '../services/api';

interface Summary {
  strengths: string[];
  areas_for_improvement: string[];
  technical_assessment: {
    score: number;
    feedback: string;
  };
  cultural_fit: {
    score: number;
    feedback: string;
  };
  overall_recommendation: string;
  next_steps: string[];
}

interface VisualData {
  candidate_name: string;
  position: string;
  skill_ratings: Array<{name: string, score: number}>;
  strengths: Array<{text: string, score: number}>;
  improvements: Array<{text: string, score: number}>;
  recommendation_score: number;
  recommendation_text: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`interview-tabpanel-${index}`}
      aria-labelledby={`interview-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ pt: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const Summary = () => {
  const navigate = useNavigate();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [visualData, setVisualData] = useState<VisualData | null>(null);
  const [loading, setLoading] = useState(true);
  const [visualLoading, setVisualLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [visualError, setVisualError] = useState<string | null>(null);
  const [selfRating, setSelfRating] = useState<number | null>(0);
  const [feedback, setFeedback] = useState('');
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    // Get summary from session storage
    const savedSummary = sessionStorage.getItem('interviewSummary');
    
    if (savedSummary) {
      try {
        const parsedSummary = JSON.parse(savedSummary);
        setSummary(parsedSummary);
      } catch (err) {
        setError('Could not load interview summary.');
        console.error(err);
      }
    } else {
      setError('No interview summary found. Please complete an interview first.');
    }
    
    setLoading(false);

    // Fetch visual data from API
    fetchVisualData();
  }, []);

  const fetchVisualData = async () => {
    try {
      setVisualLoading(true);
      const response = await api.get('/visual_summary');
      
      if (response.data.status === 'success') {
        // Validate the visual data before setting it
        const data = response.data.visual_data;
        
        // Ensure we have a valid object
        if (!data || typeof data !== 'object') {
          console.error('Invalid visual data structure:', data);
          setVisualError('Invalid visual data structure received from server.');
          setVisualData(null);
          return;
        }
        
        // Create a validated copy of the data with default values for missing properties
        const validatedData: VisualData = {
          candidate_name: data.candidate_name || 'Candidate',
          position: data.position || 'Position',
          skill_ratings: [],
          strengths: [],
          improvements: [],
          recommendation_score: typeof data.recommendation_score === 'number' ? data.recommendation_score : 70,
          recommendation_text: data.recommendation_text || 'Candidate shows potential for the role.'
        };
        
        // Validate skill_ratings
        if (Array.isArray(data.skill_ratings)) {
          validatedData.skill_ratings = data.skill_ratings
            .filter((skill: any) => skill && typeof skill === 'object')
            .map((skill: any) => ({
              name: skill.name || 'Unnamed Skill',
              score: typeof skill.score === 'number' ? skill.score : 50
            }));
        }
        
        // Validate strengths
        if (Array.isArray(data.strengths)) {
          validatedData.strengths = data.strengths
            .filter((item: any) => item && typeof item === 'object')
            .map((item: any) => ({
              text: item.text || 'Unnamed Strength',
              score: typeof item.score === 'number' ? item.score : 75
            }));
        }
        
        // Validate improvements
        if (Array.isArray(data.improvements)) {
          validatedData.improvements = data.improvements
            .filter((item: any) => item && typeof item === 'object')
            .map((item: any) => ({
              text: item.text || 'Unnamed Area',
              score: typeof item.score === 'number' ? item.score : 45
            }));
        }
        
        // Add default items if arrays are empty
        if (validatedData.skill_ratings.length === 0) {
          validatedData.skill_ratings = [
            { name: 'Technical Knowledge', score: 65 },
            { name: 'Problem Solving', score: 75 },
            { name: 'Communication', score: 70 }
          ];
        }
        
        if (validatedData.strengths.length === 0) {
          validatedData.strengths = [
            { text: 'Communication Skills', score: 85 },
            { text: 'Technical Knowledge', score: 80 }
          ];
        }
        
        if (validatedData.improvements.length === 0) {
          validatedData.improvements = [
            { text: 'Documentation', score: 50 },
            { text: 'Specific Examples', score: 40 }
          ];
        }
        
        console.log('Validated visual data:', validatedData);
        setVisualData(validatedData);
      } else {
        setVisualError('Could not load visual data. ' + (response.data.error || ''));
      }
    } catch (err) {
      console.error('Error fetching visual data:', err);
      setVisualError('Failed to load visual data. The interview may not be complete.');
    } finally {
      setVisualLoading(false);
    }
  };

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handlePrint = () => {
    window.print();
  };

  const handleDownload = () => {
    // This would typically use a library like jsPDF to generate a PDF
    alert('Download functionality would be implemented here');
  };

  const handleFeedbackSubmit = () => {
    // Would typically send this to an API
    alert(`Feedback submitted: ${selfRating} stars, "${feedback}"`);
  };

  if (loading) {
    return (
      <Box sx={{ textAlign: 'center', mt: 4 }}>
        <CircularProgress />
        <Typography sx={{ mt: 2 }}>Loading summary...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
        <Button
          variant="contained"
          startIcon={<HomeIcon />}
          onClick={() => navigate('/')}
        >
          Return to Dashboard
        </Button>
      </Box>
    );
  }

  if (!summary) {
    return (
      <Box>
        <Alert severity="warning" sx={{ mb: 3 }}>
          No interview summary available. Please complete an interview first.
        </Alert>
        <Button
          variant="contained"
          startIcon={<HomeIcon />}
          onClick={() => navigate('/')}
        >
          Start New Interview
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Interview Summary</Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<PrintIcon />}
            onClick={handlePrint}
            sx={{ mr: 1 }}
          >
            Print
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleDownload}
          >
            Download PDF
          </Button>
        </Box>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          aria-label="interview summary tabs"
          variant="fullWidth"
        >
          <Tab icon={<AssessmentIcon />} label="Standard View" id="interview-tab-0" />
          <Tab icon={<BarChartIcon />} label="Visual Analytics" id="interview-tab-1" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h5" gutterBottom>
              Overall Recommendation
            </Typography>
            <Typography variant="body1" paragraph>
              {summary?.overall_recommendation || "No recommendation available."}
            </Typography>
            
            <Divider sx={{ my: 2 }} />
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Technical Assessment
                </Typography>
                {summary?.technical_assessment ? (
                  <>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Rating 
                        value={summary.technical_assessment.score || 0} 
                        readOnly 
                        precision={0.5}
                        sx={{ mr: 1 }}
                      />
                      <Typography variant="body2">
                        ({summary.technical_assessment.score || 0}/5)
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      {summary.technical_assessment.feedback || "No feedback available"}
                    </Typography>
                  </>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    Technical assessment information not available
                  </Typography>
                )}
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Cultural Fit
                </Typography>
                {summary?.cultural_fit ? (
                  <>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Rating 
                        value={summary.cultural_fit.score || 0} 
                        readOnly 
                        precision={0.5}
                        sx={{ mr: 1 }}
                      />
                      <Typography variant="body2">
                        ({summary.cultural_fit.score || 0}/5)
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      {summary.cultural_fit.feedback || "No feedback available"}
                    </Typography>
                  </>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    Cultural fit information not available
                  </Typography>
                )}
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ThumbUpIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="h6">Strengths</Typography>
              </Box>
              <Stack spacing={1}>
                {summary?.strengths && Array.isArray(summary.strengths) && summary.strengths.length > 0 ? (
                  summary.strengths.map((strength, index) => (
                    <Typography key={index} variant="body2">
                      • {strength}
                    </Typography>
                  ))
                ) : (
                  <Typography variant="body2">
                    No strengths identified yet.
                  </Typography>
                )}
              </Stack>
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ThumbDownIcon color="error" sx={{ mr: 1 }} />
                <Typography variant="h6">Areas for Improvement</Typography>
              </Box>
              <Stack spacing={1}>
                {summary?.areas_for_improvement && Array.isArray(summary.areas_for_improvement) && summary.areas_for_improvement.length > 0 ? (
                  summary.areas_for_improvement.map((area, index) => (
                    <Typography key={index} variant="body2">
                      • {area}
                    </Typography>
                  ))
                ) : (
                  <Typography variant="body2">
                    No areas for improvement identified yet.
                  </Typography>
                )}
              </Stack>
            </Paper>
          </Grid>
        </Grid>

        <Card sx={{ my: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Next Steps
            </Typography>
            <Stack spacing={1} direction="row" flexWrap="wrap" useFlexGap>
              {summary?.next_steps && Array.isArray(summary.next_steps) && summary.next_steps.length > 0 ? (
                summary.next_steps.map((step, index) => (
                  <Chip 
                    key={index} 
                    label={step} 
                    color="primary" 
                    variant="outlined" 
                    sx={{ mb: 1 }}
                  />
                ))
              ) : (
                <Typography variant="body2">
                  No next steps available.
                </Typography>
              )}
            </Stack>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        {visualLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
            <CircularProgress />
            <Typography sx={{ ml: 2 }}>Loading visual data...</Typography>
          </Box>
        ) : visualError ? (
          <Alert severity="warning" sx={{ mb: 3 }}>
            {visualError}
          </Alert>
        ) : visualData ? (
          <InterviewSummaryVisual summaryData={visualData} />
        ) : (
          <Alert severity="info">
            Visual data is not available for this interview. Complete the interview to see visualizations.
          </Alert>
        )}
      </TabPanel>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Your Self-Assessment
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          How would you rate your own performance in this interview?
        </Typography>
        
        <Box sx={{ mb: 2 }}>
          <Rating
            name="self-rating"
            value={selfRating}
            onChange={(_, newValue) => {
              setSelfRating(newValue);
            }}
            size="large"
          />
        </Box>
        
        <TextField
          fullWidth
          label="Your feedback (optional)"
          multiline
          rows={4}
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="Share your thoughts on the interview process..."
          variant="outlined"
          sx={{ mb: 2 }}
        />
        
        <Button 
          variant="contained" 
          onClick={handleFeedbackSubmit} 
          disabled={!selfRating}
        >
          Submit Feedback
        </Button>
      </Paper>
      
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <Button
          variant="contained"
          size="large"
          color="secondary"
          startIcon={<HomeIcon />}
          onClick={() => navigate('/')}
        >
          Start New Interview
        </Button>
      </Box>
    </Box>
  );
};

export default Summary; 