import { AppBar, Toolbar, Typography, Button, Box, useMediaQuery, useTheme } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import PsychologyIcon from '@mui/icons-material/Psychology';

const Header = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <AppBar position="static" color="default" elevation={0} sx={{ borderBottom: '1px solid rgba(0, 0, 0, 0.12)' }}>
      <Toolbar>
        <RouterLink to="/" style={{ textDecoration: 'none', color: 'inherit', display: 'flex', alignItems: 'center' }}>
          <PsychologyIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6" color="primary" noWrap sx={{ flexGrow: 1, fontWeight: 600 }}>
            AI Interview Agent
          </Typography>
        </RouterLink>
        
        <Box sx={{ flexGrow: 1 }} />
        
        {!isMobile && (
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button 
              color="inherit" 
              component={RouterLink} 
              to="/"
            >
              Dashboard
            </Button>
            <Button 
              color="primary" 
              variant="contained" 
              component={RouterLink} 
              to="/interview"
            >
              Start Interview
            </Button>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default Header; 