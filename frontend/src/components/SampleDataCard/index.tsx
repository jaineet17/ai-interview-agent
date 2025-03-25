import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import WorkIcon from '@mui/icons-material/Work';
import BusinessIcon from '@mui/icons-material/Business';
import PersonIcon from '@mui/icons-material/Person';
import CheckIcon from '@mui/icons-material/Check';

interface SampleDataCardProps {
  onLoadSampleData: () => void;
}

const SampleDataCard = ({ onLoadSampleData }: SampleDataCardProps) => {
  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Sample Data Preview
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Use our pre-configured sample data to quickly test the interview process.
        </Typography>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center' }}>
                <WorkIcon sx={{ mr: 1, color: 'primary.main' }} />
                Job: Senior Software Engineer
              </Typography>
              <List dense sx={{ pl: 4 }}>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 24 }}>
                    <CheckIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="Full-stack development" />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 24 }}>
                    <CheckIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="Python, Django, React" />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 24 }}>
                    <CheckIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="5+ years experience" />
                </ListItem>
              </List>
            </Box>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center' }}>
                <BusinessIcon sx={{ mr: 1, color: 'secondary.main' }} />
                Company: TechCorp Inc.
              </Typography>
              <List dense sx={{ pl: 4 }}>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 24 }}>
                    <CheckIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="Cloud & AI solutions" />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 24 }}>
                    <CheckIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="500-1000 employees" />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 24 }}>
                    <CheckIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="Collaborative culture" />
                </ListItem>
              </List>
            </Box>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center' }}>
                <PersonIcon sx={{ mr: 1, color: 'error.main' }} />
                Candidate: John Smith
              </Typography>
              <List dense sx={{ pl: 4 }}>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 24 }}>
                    <CheckIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="8 years experience" />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 24 }}>
                    <CheckIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="CS degree from Stanford" />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 24 }}>
                    <CheckIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="AWS certified" />
                </ListItem>
              </List>
            </Box>
          </Grid>
        </Grid>
        
        <Divider sx={{ my: 2 }} />
        
        <Box sx={{ display: 'flex', justifyContent: 'center' }}>
          <Button
            variant="contained"
            color="secondary"
            onClick={onLoadSampleData}
            sx={{ minWidth: 200 }}
          >
            Use Sample Data
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default SampleDataCard; 