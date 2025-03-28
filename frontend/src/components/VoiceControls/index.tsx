import React, { useState, useEffect } from 'react';
import { 
  Box, 
  IconButton, 
  Tooltip, 
  Typography,
  Badge,
  Switch,
  FormControlLabel,
  Paper,
  Chip,
  keyframes
} from '@mui/material';
import MicIcon from '@mui/icons-material/Mic';
import MicOffIcon from '@mui/icons-material/MicOff';
import VolumeUpIcon from '@mui/icons-material/VolumeUp';
import VolumeOffIcon from '@mui/icons-material/VolumeOff';

interface VoiceControlsProps {
  onSpeechResult?: (text: string) => void;
  message?: string;
  enabled?: boolean;
  onVoiceStateChange?: (enabled: boolean) => void;
}

// Check if the browser supports the Web Speech API
const speechRecognitionSupported = 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window;
const speechSynthesisSupported = 'speechSynthesis' in window;

// Define the pulse animation
const pulse = keyframes`
  0% { opacity: 1; }
  50% { opacity: 0.6; }
  100% { opacity: 1; }
`;

const VoiceControls: React.FC<VoiceControlsProps> = ({ 
  onSpeechResult, 
  message,
  enabled = true,
  onVoiceStateChange
}) => {
  const [isListening, setIsListening] = useState<boolean>(false);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [speechEnabled, setSpeechEnabled] = useState<boolean>(enabled);
  const [sttEnabled] = useState<boolean>(speechRecognitionSupported && enabled);
  const [ttsEnabled, setTTSEnabled] = useState<boolean>(speechSynthesisSupported && enabled);
  const [recognitionInstance, setRecognitionInstance] = useState<any>(null);

  // Initialize speech recognition
  useEffect(() => {
    if (speechRecognitionSupported && speechEnabled && sttEnabled) {
      // @ts-ignore - Using vendor prefixed versions if needed
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';
      
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        if (onSpeechResult) {
          onSpeechResult(transcript);
        }
        setIsListening(false);
      };
      
      recognition.onerror = (event: any) => {
        console.error('Speech recognition error', event.error);
        setIsListening(false);
      };
      
      recognition.onend = () => {
        setIsListening(false);
      };
      
      setRecognitionInstance(recognition);
      
      return () => {
        recognition.abort();
      };
    }
  }, [speechEnabled, sttEnabled, onSpeechResult]);

  // Speak the message when it changes
  useEffect(() => {
    if (speechSynthesisSupported && speechEnabled && ttsEnabled && message && !isSpeaking) {
      speakMessage(message);
    }
  }, [message, ttsEnabled, speechEnabled]);

  // Notify parent component when speech state changes
  useEffect(() => {
    if (onVoiceStateChange) {
      onVoiceStateChange(speechEnabled);
    }
  }, [speechEnabled, onVoiceStateChange]);

  const toggleListening = () => {
    if (!speechRecognitionSupported || !speechEnabled || !sttEnabled) {
      return;
    }
    
    if (isListening) {
      recognitionInstance?.abort();
      setIsListening(false);
    } else {
      recognitionInstance?.start();
      setIsListening(true);
    }
  };

  const speakMessage = (text: string) => {
    if (!speechSynthesisSupported || !ttsEnabled || !text || isSpeaking) {
      return;
    }
    
    try {
      // First cancel any ongoing speech
      window.speechSynthesis.cancel();
      
      const utterance = new SpeechSynthesisUtterance(text);
      
      // Select a voice - prefer a female voice if available
      const voices = window.speechSynthesis.getVoices();
      if (voices.length > 0) {
        // Look for a good voice - prefer female English voices
        const preferredVoice = voices.find(voice => 
          voice.lang.includes('en') && voice.name.includes('Female')
        ) || voices.find(voice => 
          voice.lang.includes('en')
        ) || voices[0];
        
        utterance.voice = preferredVoice;
      }
      
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      
      setIsSpeaking(true);
      
      utterance.onend = () => {
        setIsSpeaking(false);
      };
      
      utterance.onerror = (event) => {
        console.error('Speech synthesis error', event);
        setIsSpeaking(false);
        // Don't rethrow the error, just log it and continue
      };
      
      window.speechSynthesis.speak(utterance);
    } catch (error) {
      console.error('Error setting up speech synthesis:', error);
      setIsSpeaking(false);
    }
  };

  const toggleTTS = () => {
    if (!speechSynthesisSupported || !speechEnabled) {
      return;
    }
    
    const newTTSState = !ttsEnabled;
    setTTSEnabled(newTTSState);
    
    if (!newTTSState) {
      // Stop any ongoing speech
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };
  
  const handleSpeechEnabledChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newEnabledState = event.target.checked;
    setSpeechEnabled(newEnabledState);
    
    if (!newEnabledState) {
      // Stop any ongoing speech and recognition
      window.speechSynthesis.cancel();
      recognitionInstance?.abort();
      setIsSpeaking(false);
      setIsListening(false);
    }
  };

  if (!speechRecognitionSupported && !speechSynthesisSupported) {
    return (
      <Paper sx={{ p: 1, mb: 1 }}>
        <Typography variant="body2" color="error">
          Voice controls are not supported in your browser.
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 1, display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <FormControlLabel
          control={
            <Switch
              checked={speechEnabled}
              onChange={handleSpeechEnabledChange}
              color="primary"
            />
          }
          label="Voice Controls"
        />
        
        {isListening && speechEnabled && (
          <Chip 
            label="Listening..." 
            color="error" 
            size="small" 
            sx={{ ml: 1, animation: `${pulse} 1.5s infinite` }}
          />
        )}
        
        {isSpeaking && speechEnabled && (
          <Chip 
            label="Speaking..." 
            color="primary" 
            size="small" 
            sx={{ ml: 1 }}
          />
        )}
      </Box>
      
      <Box>
        {speechRecognitionSupported && speechEnabled && (
          <Tooltip title={isListening ? "Stop listening" : "Start voice input"}>
            <span>
              <IconButton 
                onClick={toggleListening} 
                color="primary"
                disabled={!sttEnabled}
              >
                <Badge color="error" variant="dot" invisible={!isListening}>
                  {isListening ? <MicIcon /> : <MicOffIcon />}
                </Badge>
              </IconButton>
            </span>
          </Tooltip>
        )}
        
        {speechSynthesisSupported && speechEnabled && (
          <Tooltip title={ttsEnabled ? "Turn off text-to-speech" : "Turn on text-to-speech"}>
            <IconButton 
              onClick={toggleTTS} 
              color="primary"
            >
              <Badge color="error" variant="dot" invisible={!isSpeaking}>
                {ttsEnabled ? <VolumeUpIcon /> : <VolumeOffIcon />}
              </Badge>
            </IconButton>
          </Tooltip>
        )}
      </Box>
    </Paper>
  );
};

export default VoiceControls; 