import { Box, Typography, Link, Container } from '@mui/material';

const Footer = () => {
  return (
    <Box
      component="footer"
      sx={{
        py: 3,
        px: 2,
        mt: 'auto',
        backgroundColor: (theme) => theme.palette.grey[50],
        borderTop: '1px solid rgba(0, 0, 0, 0.12)',
      }}
    >
      <Container maxWidth="lg">
        <Typography variant="body2" color="text.secondary" align="center">
          {'© '}
          {new Date().getFullYear()}
          {' '}
          <Link color="inherit" href="https://github.com/yourusername/ai-interview-agent">
            AI Interview Agent
          </Link>
          {' - Built with '}
          <Link color="inherit" href="https://reactjs.org/">
            React
          </Link>
          {' and '}
          <Link color="inherit" href="https://mui.com/">
            Material UI
          </Link>
        </Typography>
      </Container>
    </Box>
  );
};

export default Footer; 