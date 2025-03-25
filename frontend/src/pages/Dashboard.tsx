import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Alert,
  AlertTitle,
  Divider,
  Tab,
  Tabs,
  FormControlLabel,
  Switch,
  Tooltip,
} from '@mui/material';
import FileUploadIcon from '@mui/icons-material/FileUpload';
import DataObjectIcon from '@mui/icons-material/DataObject';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import SportsEsportsIcon from '@mui/icons-material/SportsEsports';
import FileUploader from '../components/FileUploader';
import SampleDataCard from '../components/SampleDataCard';

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
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `simple-tab-${index}`,
    'aria-controls': `simple-tabpanel-${index}`,
  };
}

const Dashboard = () => {
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const [job, setJob] = useState<File | null>(null);
  const [company, setCompany] = useState<File | null>(null);
  const [candidate, setCandidate] = useState<File | null>(null);
  const [usingSampleData, setUsingSampleData] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [demoMode, setDemoMode] = useState(false);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleJobUpload = (file: File) => {
    setJob(file);
    setError(null);
  };

  const handleCompanyUpload = (file: File) => {
    setCompany(file);
    setError(null);
  };

  const handleCandidateUpload = (file: File) => {
    setCandidate(file);
    setError(null);
  };

  const handleLoadSampleData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Call API to load sample data
      const response = await fetch('/api/load_sample_data', {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Failed to load sample data');
      }
      
      setUsingSampleData(true);
      setSuccess('Sample data loaded successfully!');
      
      setTimeout(() => {
        setSuccess(null);
      }, 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const handleUploadData = async () => {
    if (tabValue === 0 && (!job || !company || !candidate)) {
      setError('Please upload all required files: Job, Company, and Candidate');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      if (tabValue === 0) {
        // Upload files one by one using the new API endpoints
        const uploadFile = async (file: File, type: string) => {
          const formData = new FormData();
          formData.append('file', file);
          
          const response = await fetch(`/api/upload/${type}`, {
            method: 'POST',
            body: formData,
          });
          
          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Failed to upload ${type} data`);
          }
          
          return await response.json();
        };
        
        // Upload all files sequentially
        if (job) await uploadFile(job, 'job');
        if (company) await uploadFile(company, 'company');
        if (candidate) await uploadFile(candidate, 'candidate');
      }
      
      // Initialize interview
      const initResponse = await fetch('/api/initialize_interview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          demo_mode: demoMode || tabValue === 1  // Enable demo mode if toggle is on or sample data is selected
        }),
      });
      
      if (!initResponse.ok) {
        const errorData = await initResponse.json();
        throw new Error(errorData.error || 'Failed to initialize interview');
      }
      
      setSuccess('Interview initialized successfully!');
      
      // Navigate to interview page after short delay
      setTimeout(() => {
        navigate('/interview');
      }, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Interview Setup
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Configure your interview by uploading data about the job, company, and candidate.
      </Typography>

      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 2 }}
          onClose={() => setError(null)}
        >
          <AlertTitle>Error</AlertTitle>
          {error}
        </Alert>
      )}

      {success && (
        <Alert 
          severity="success" 
          sx={{ mb: 2 }}
          onClose={() => setSuccess(null)}
        >
          <AlertTitle>Success</AlertTitle>
          {success}
        </Alert>
      )}

      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="data source tabs">
              <Tab 
                icon={<FileUploadIcon />} 
                label="Upload Files" 
                {...a11yProps(0)}
                sx={{ textTransform: 'none' }}
              />
              <Tab 
                icon={<DataObjectIcon />} 
                label="Use Sample Data" 
                {...a11yProps(1)}
                sx={{ textTransform: 'none' }}
              />
            </Tabs>
          </Box>
          
          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <FileUploader
                  title="Job Description"
                  description="Upload job description (PDF, DOCX, TXT, or JSON)"
                  acceptedFileTypes={['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain', 'application/json']}
                  onFileUpload={handleJobUpload}
                  file={job}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <FileUploader
                  title="Company Information"
                  description="Upload company information (PDF, DOCX, TXT, or JSON)"
                  acceptedFileTypes={['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain', 'application/json']}
                  onFileUpload={handleCompanyUpload}
                  file={company}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <FileUploader
                  title="Candidate Resume"
                  description="Upload candidate resume (PDF, DOCX, TXT, or JSON)"
                  acceptedFileTypes={['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain', 'application/json']}
                  onFileUpload={handleCandidateUpload}
                  file={candidate}
                />
              </Grid>
            </Grid>
          </TabPanel>
          
          <TabPanel value={tabValue} index={1}>
            <SampleDataCard onLoadSampleData={handleLoadSampleData} />
          </TabPanel>
          
          <Divider sx={{ my: 3 }} />
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Tooltip title="Enable demo mode for a simpler interview experience. The AI will generate shorter responses and ask fewer follow-up questions.">
              <FormControlLabel
                control={
                  <Switch
                    checked={demoMode}
                    onChange={(e) => setDemoMode(e.target.checked)}
                    color="primary"
                  />
                }
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <SportsEsportsIcon sx={{ mr: 1 }} />
                    <Typography>Demo Mode</Typography>
                  </Box>
                }
              />
            </Tooltip>
            
            <Button
              variant="contained"
              color="primary"
              size="large"
              startIcon={<PlayArrowIcon />}
              onClick={handleUploadData}
              disabled={loading || (tabValue === 0 && (!job || !company || !candidate)) || (tabValue === 1 && !usingSampleData)}
            >
              Start Interview
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Dashboard; 