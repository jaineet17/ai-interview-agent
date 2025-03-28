import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Avatar,
  CircularProgress,
  Card,
  CardContent,
  IconButton,
  Button,
  Tooltip,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import { startInterview, processResponse } from '../services/api';
import VoiceControls from '../components/VoiceControls';

const Interview = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const [userInput, setUserInput] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [interviewComplete, setInterviewComplete] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [voiceEnabled, setVoiceEnabled] = useState<boolean>(true);
  const [latestAgentMessage, setLatestAgentMessage] = useState<string>('');

  // Scroll to bottom whenever messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Update latest agent message for TTS when messages change
  useEffect(() => {
    if (messages.length > 0) {
      const agentMessages = messages.filter(m => m.isAgent);
      if (agentMessages.length > 0) {
        setLatestAgentMessage(agentMessages[agentMessages.length - 1].content);
      }
    }
  }, [messages]);

  // Start the interview on component mount
  useEffect(() => {
    const initInterview = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const response = await startInterview();
        
        // Handle different response structures
        if (response.question) {
          // Standard response with question
          setMessages([
            {
              isAgent: true,
              content: response.question.question,
              timestamp: new Date(),
            },
          ]);
        } else if (response.status === 'success' && response.message) {
          // Success message response
          setMessages([
            {
              isAgent: true,
              content: response.message,
              timestamp: new Date(),
            },
          ]);
        } else {
          // Fallback message if structure is unexpected
          setMessages([
            {
              isAgent: true,
              content: "Welcome to your interview! Please tell me a bit about yourself and your interest in this position.",
              timestamp: new Date(),
            },
          ]);
        }
      } catch (err) {
        console.error('Interview start error:', err);
        setError(err instanceof Error ? err.message : 'Failed to start interview. Please try again or return to dashboard.');
        
        // Add a message to help the user
        setMessages([
          {
            isAgent: true,
            content: "There was an issue starting the interview. You may need to go back to the dashboard and initialize the interview first.",
            timestamp: new Date(),
          },
        ]);
      } finally {
        setLoading(false);
      }
    };

    initInterview();
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUserInput(e.target.value);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSendMessage = async () => {
    if (!userInput.trim() || isSending) return;

    const userMessage = {
      isAgent: false,
      content: userInput,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setUserInput('');
    setIsSending(true);

    try {
      // No need to show typing indicator
      
      const response = await processResponse(userMessage.content);

      if (response.status === 'complete') {
        setInterviewComplete(true);
        setMessages((prev) => [
          ...prev,
          {
            isAgent: true,
            content: response.closing_remarks,
            timestamp: new Date(),
          },
        ]);
        
        // Store summary in session storage for the summary page
        sessionStorage.setItem('interviewSummary', JSON.stringify(response.summary));
        
        // Navigate to summary page after a delay
        setTimeout(() => {
          navigate('/summary');
        }, 3000);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            isAgent: true,
            content: response.question && response.question.question 
              ? `${response.acknowledgment || ''}${response.acknowledgment ? ' ' : ''}${response.question.question}`
              : response.acknowledgment || 'Let me think about what to ask next...',
            timestamp: new Date(),
          },
        ]);
      }
    } catch (err) {
      setError('Failed to process your response. Please try again.');
      console.error(err);
    } finally {
      setIsSending(false);
    }
  };

  // Handle voice input
  const handleSpeechResult = (text: string) => {
    setUserInput(text);
    // Auto-submit after voice input with a small delay
    setTimeout(() => {
      handleSendMessage();
    }, 500);
  };

  // Toggle voice control state
  const handleVoiceStateChange = (enabled: boolean) => {
    setVoiceEnabled(enabled);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h5" gutterBottom>
            Technical Interview
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Respond to the questions as you would in a real interview. The AI interviewer will adapt to your responses.
            {voiceEnabled && " Voice controls are enabled - you can speak your answers and hear the interviewer's questions."}
          </Typography>
        </CardContent>
      </Card>

      {/* Voice controls */}
      <VoiceControls 
        onSpeechResult={handleSpeechResult}
        message={latestAgentMessage}
        enabled={voiceEnabled}
        onVoiceStateChange={handleVoiceStateChange}
      />

      {error && (
        <Paper sx={{ p: 2, mb: 2, bgcolor: 'error.light', color: 'error.contrastText' }}>
          <Typography>{error}</Typography>
        </Paper>
      )}

      <Paper
        sx={{
          flexGrow: 1,
          mb: 2,
          p: 2,
          height: '60vh',
          maxHeight: '60vh',
          overflow: 'auto',
          bgcolor: 'background.default',
        }}
      >
        {messages.map((message, index) => (
          <Box
            key={index}
            sx={{
              display: 'flex',
              justifyContent: message.isAgent ? 'flex-start' : 'flex-end',
              mb: 2,
            }}
          >
            {message.isAgent && (
              <Avatar sx={{ bgcolor: 'primary.main', mr: 1 }}>
                <SmartToyIcon />
              </Avatar>
            )}
            <Paper
              sx={{
                p: 2,
                maxWidth: '70%',
                bgcolor: message.isAgent ? 'primary.light' : 'secondary.light',
                color: message.isAgent ? 'primary.contrastText' : 'secondary.contrastText',
              }}
            >
              <Typography variant="body1">{message.content}</Typography>
              <Typography variant="caption" sx={{ display: 'block', mt: 1, opacity: 0.7 }}>
                {new Date(message.timestamp).toLocaleTimeString()}
              </Typography>
            </Paper>
            {!message.isAgent && (
              <Avatar sx={{ bgcolor: 'secondary.main', ml: 1 }}>
                <PersonIcon />
              </Avatar>
            )}
          </Box>
        ))}
        <div ref={messagesEndRef} />
      </Paper>

      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder={voiceEnabled ? "Type or speak your response..." : "Type your response..."}
            value={userInput}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            disabled={isSending || interviewComplete}
            multiline
            rows={2}
            sx={{ mr: 1 }}
          />
          <Tooltip title="Send message">
            <IconButton
              color="primary"
              onClick={handleSendMessage}
              disabled={!userInput.trim() || isSending || interviewComplete}
              size="large"
            >
              <SendIcon />
            </IconButton>
          </Tooltip>
        </Box>
        {interviewComplete && (
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Interview complete! Redirecting to summary...
            </Typography>
            <Button variant="contained" onClick={() => navigate('/summary')}>
              Go to Summary
            </Button>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default Interview; 