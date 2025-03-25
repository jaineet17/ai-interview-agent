import { useState } from 'react';
import { 
  Paper, 
  Box, 
  Typography, 
  Button, 
  LinearProgress, 
  Chip,
  IconButton
} from '@mui/material';
import { styled } from '@mui/material/styles';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import DeleteIcon from '@mui/icons-material/Delete';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import TextSnippetIcon from '@mui/icons-material/TextSnippet';
import DataObjectIcon from '@mui/icons-material/DataObject';
import DescriptionIcon from '@mui/icons-material/Description';

const VisuallyHiddenInput = styled('input')({
  clip: 'rect(0 0 0 0)',
  clipPath: 'inset(50%)',
  height: 1,
  overflow: 'hidden',
  position: 'absolute',
  bottom: 0,
  left: 0,
  whiteSpace: 'nowrap',
  width: 1,
});

interface FileUploaderProps {
  title: string;
  description: string;
  acceptedFileTypes: string[];
  onFileUpload: (file: File) => void;
  file: File | null;
}

const FileUploader = ({
  title,
  description,
  acceptedFileTypes,
  onFileUpload,
  file,
}: FileUploaderProps) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const selectedFile = event.target.files[0];
      
      // Check file type
      if (!acceptedFileTypes.includes(selectedFile.type)) {
        setError('File type not supported. Please upload a PDF, DOCX, TXT, or JSON file.');
        return;
      }
      
      // Check file size (limit to 10MB)
      if (selectedFile.size > 10 * 1024 * 1024) {
        setError('File size exceeds 10MB limit.');
        return;
      }
      
      // Simulate upload progress
      setIsUploading(true);
      setError(null);
      
      let progress = 0;
      const interval = setInterval(() => {
        progress += 10;
        setUploadProgress(progress);
        
        if (progress >= 100) {
          clearInterval(interval);
          setIsUploading(false);
          onFileUpload(selectedFile);
        }
      }, 150);
    }
  };

  const getFileIcon = () => {
    if (!file) return <CloudUploadIcon fontSize="large" />;
    
    switch (file.type) {
      case 'application/pdf':
        return <PictureAsPdfIcon fontSize="large" color="error" />;
      case 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        return <DescriptionIcon fontSize="large" color="primary" />;
      case 'text/plain':
        return <TextSnippetIcon fontSize="large" color="success" />;
      case 'application/json':
        return <DataObjectIcon fontSize="large" color="warning" />;
      default:
        return <CloudUploadIcon fontSize="large" />;
    }
  };

  const getFileTypeLabel = () => {
    if (!file) return '';
    
    switch (file.type) {
      case 'application/pdf':
        return 'PDF';
      case 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        return 'DOCX';
      case 'text/plain':
        return 'TXT';
      case 'application/json':
        return 'JSON';
      default:
        return file.type.split('/')[1].toUpperCase();
    }
  };

  const handleClearFile = () => {
    onFileUpload(null as unknown as File);
    setError(null);
  };

  return (
    <Paper 
      sx={{ 
        p: 3, 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center',
        height: '100%',
        backgroundColor: (theme) => theme.palette.grey[50],
        border: '1px dashed',
        borderColor: (theme) => theme.palette.divider,
        transition: 'all 0.3s ease',
        '&:hover': {
          borderColor: (theme) => theme.palette.primary.main,
          backgroundColor: (theme) => theme.palette.background.paper,
        }
      }}
    >
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      
      <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 2 }}>
        {description}
      </Typography>
      
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center',
          flexDirection: 'column',
          flexGrow: 1,
          width: '100%'
        }}
      >
        {isUploading ? (
          <Box sx={{ width: '100%', mt: 2 }}>
            <LinearProgress variant="determinate" value={uploadProgress} />
            <Typography variant="caption" sx={{ mt: 1, display: 'block', textAlign: 'center' }}>
              Uploading... {uploadProgress}%
            </Typography>
          </Box>
        ) : file ? (
          <Box 
            sx={{ 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center',
              p: 2
            }}
          >
            {getFileIcon()}
            <Box sx={{ mt: 2, textAlign: 'center' }}>
              <Chip 
                label={getFileTypeLabel()} 
                size="small" 
                sx={{ mb: 1 }} 
                color={
                  file.type === 'application/pdf' ? 'error' : 
                  file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ? 'primary' :
                  file.type === 'text/plain' ? 'success' : 'warning'
                }
              />
              <Typography 
                variant="body2" 
                noWrap 
                sx={{ 
                  maxWidth: '100%', 
                  display: 'block',
                  fontWeight: 'medium'
                }}
              >
                {file.name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {(file.size / 1024).toFixed(1)} KB
              </Typography>
            </Box>
            <IconButton 
              color="error" 
              sx={{ mt: 1 }} 
              onClick={handleClearFile}
              size="small"
            >
              <DeleteIcon />
            </IconButton>
          </Box>
        ) : (
          <Box>
            <Button
              component="label"
              variant="outlined"
              startIcon={<CloudUploadIcon />}
              sx={{ mb: 1 }}
            >
              Upload File
              <VisuallyHiddenInput 
                type="file" 
                onChange={handleFileChange} 
                accept={acceptedFileTypes.join(',')}
              />
            </Button>
          </Box>
        )}
        
        {error && (
          <Typography 
            variant="caption" 
            color="error" 
            sx={{ mt: 1, textAlign: 'center' }}
          >
            {error}
          </Typography>
        )}
      </Box>
    </Paper>
  );
};

export default FileUploader; 