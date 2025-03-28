import React from 'react';
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  ResponsiveContainer, Cell
} from 'recharts';
import { Box, Typography, Paper, Grid, useTheme, Alert } from '@mui/material';

interface SkillRating {
  name: string;
  score: number;
}

interface StrengthOrImprovement {
  text?: string;
  score?: number;
  // New fields for more complex data structures
  strength?: string;
  evidence?: string;
  rating?: number | string;
  area?: string;
  suggestion?: string;
  name?: string;
  [key: string]: any; // Allow any other properties
}

interface VisualSummaryData {
  candidate_name: string;
  position: string;
  skill_ratings: SkillRating[];
  strengths: StrengthOrImprovement[];
  improvements: StrengthOrImprovement[];
  recommendation_score: number;
  recommendation_text: string;
}

interface InterviewSummaryVisualProps {
  summaryData: VisualSummaryData;
}

const InterviewSummaryVisual: React.FC<InterviewSummaryVisualProps> = ({ summaryData }) => {
  const theme = useTheme();
  
  // Check if summaryData is completely undefined
  if (!summaryData) {
    return (
      <Alert severity="error">
        No visual summary data available. Please complete an interview to see visualizations.
      </Alert>
    );
  }

  // Create a default/fallback skill if needed
  const createDefaultSkill = (index: number) => ({
    subject: `Skill ${index + 1}`,
    score: 50 + (index * 10) % 50, // Vary the scores
    fullMark: 100
  });
  
  // Create default skills array with 3 items
  const defaultSkills = [
    { subject: 'Technical Knowledge', score: 65, fullMark: 100 },
    { subject: 'Problem Solving', score: 75, fullMark: 100 },
    { subject: 'Communication', score: 70, fullMark: 100 }
  ];
  
  // Process the skills with extra safety checks
  let processedSkills: any[] = [];
  
  try {
    // Check if skill_ratings exists and is an array
    if (Array.isArray(summaryData.skill_ratings)) {
      processedSkills = summaryData.skill_ratings.map((skill, index) => {
        if (!skill) {
          return createDefaultSkill(index);
        }
        
        // Safely access name and score with defaults
        const name = skill.name ?? `Skill ${index + 1}`;
        const score = typeof skill.score === 'number' ? skill.score : 50;
        
        return {
          subject: name,
          score: score,
          fullMark: 100
        };
      });
    }
    
    // If no valid skills or empty array, use defaults
    if (processedSkills.length === 0) {
      processedSkills = defaultSkills;
    }
  } catch (e) {
    console.error("Error processing skills:", e);
    processedSkills = defaultSkills;
  }
  
  // Colors for the visual elements
  const colors = {
    skills: theme.palette.primary.main,
    strengths: theme.palette.success.main,
    improvements: theme.palette.error.main,
    recommendation: theme.palette.warning.main
  };

  // Process strengths with safety checks
  let processedStrengths: any[] = [];
  try {
    if (Array.isArray(summaryData.strengths)) {
      processedStrengths = summaryData.strengths.map((s, index) => {
        if (!s) {
          return { 
            name: `Strength ${index + 1}`, 
            value: 75 + index * 5, 
            type: 'Strength' 
          };
        }
        
        // Handle different formats of strengths data
        let displayText;
        let scoreValue = 75 + index * 5; // Default score based on index
        
        if (typeof s === 'string') {
          // Simple string format
          displayText = s;
        } else if (s.text && typeof s.text === 'string') {
          // Object with text property
          displayText = s.text;
          if (typeof s.score === 'number') {
            scoreValue = s.score;
          }
        } else if (s.strength && typeof s.strength === 'string') {
          // New format: {"strength": "...", "rating": "...", "evidence": "..."}
          displayText = s.strength;
          if (typeof s.rating === 'number') {
            scoreValue = s.rating;
          }
        } else if (Object.keys(s).length === 1) {
          // Object with key being category and value being description
          // Example: {"Strength 1: Technical expertise": "description"}
          const key = Object.keys(s)[0];
          displayText = key;
        } else if (s.evidence || s.rating) {
          // Object with evidence and rating but missing strength field
          displayText = s.evidence ? `Evidence: ${s.evidence.substring(0, 15)}...` : `Strength ${index + 1}`;
        } else {
          // Fallback for unknown formats
          displayText = `Strength ${index + 1}`;
        }
        
        // Extract just the first part of the text or limit to 25 chars for display
        // If text contains a colon, take just the first part
        if (displayText.includes(':')) {
          displayText = displayText.split(':')[0].trim();
        } else if (displayText.includes('-')) {
          displayText = displayText.split('-')[0].trim();
        }
        // Limit to 25 chars max
        displayText = displayText.length > 25 ? displayText.substring(0, 22) + '...' : displayText;
        
        return { 
          name: displayText, 
          value: scoreValue, 
          type: 'Strength' 
        };
      });
    }
    
    if (processedStrengths.length === 0) {
      processedStrengths = [
        { name: "Communication Skills", value: 85, type: 'Strength' },
        { name: "Technical Knowledge", value: 80, type: 'Strength' }
      ];
    }
  } catch (e) {
    console.error("Error processing strengths:", e);
    processedStrengths = [
      { name: "Communication Skills", value: 85, type: 'Strength' },
      { name: "Technical Knowledge", value: 80, type: 'Strength' }
    ];
  }
  
  // Process improvements with safety checks
  let processedImprovements: any[] = [];
  try {
    if (Array.isArray(summaryData.improvements)) {
      processedImprovements = summaryData.improvements.map((i, index) => {
        if (!i) {
          return { 
            name: `Area ${index + 1}`, 
            value: 60 - index * 10, 
            type: 'Improvement' 
          };
        }
        
        // Handle different formats of improvement data
        let displayText;
        let scoreValue = 60 - index * 10; // Default score based on index
        
        if (typeof i === 'string') {
          // Simple string format
          displayText = i;
        } else if (i.text && typeof i.text === 'string') {
          // Object with text property
          displayText = i.text;
          if (typeof i.score === 'number') {
            scoreValue = i.score;
          }
        } else if (i.area && typeof i.area === 'string') {
          // New format: {"area": "...", "rating": "...", "suggestion": "..."}
          displayText = i.area;
          if (typeof i.rating === 'number') {
            scoreValue = i.rating;
          }
        } else if (Object.keys(i).length === 1) {
          // Object with key being category and value being description
          // Example: {"Area: React/Vue.js experience": "description"}
          const key = Object.keys(i)[0];
          displayText = key;
        } else if (i.suggestion || i.rating) {
          // Object with suggestion and rating but missing area field
          displayText = i.suggestion ? `Suggestion: ${i.suggestion.substring(0, 15)}...` : `Area ${index + 1}`;
        } else {
          // Fallback for unknown formats
          displayText = `Area ${index + 1}`;
        }
        
        // Extract just the first part of the text or limit to 25 chars for display
        // If text contains a colon, take just the first part
        if (displayText.includes(':')) {
          displayText = displayText.split(':')[0].trim();
        } else if (displayText.includes('-')) {
          displayText = displayText.split('-')[0].trim();
        }
        // Limit to 25 chars max
        displayText = displayText.length > 25 ? displayText.substring(0, 22) + '...' : displayText;
        
        return { 
          name: displayText,
          value: scoreValue, 
          type: 'Improvement' 
        };
      });
    }
    
    if (processedImprovements.length === 0) {
      processedImprovements = [
        { name: "Documentation", value: 50, type: 'Improvement' },
        { name: "Specific Examples", value: 40, type: 'Improvement' }
      ];
    }
  } catch (e) {
    console.error("Error processing improvements:", e);
    processedImprovements = [
      { name: "Documentation", value: 50, type: 'Improvement' },
      { name: "Specific Examples", value: 40, type: 'Improvement' }
    ];
  }
  
  // Safely combine strengths and improvements
  const strengthsAndImprovements = [...processedStrengths, ...processedImprovements];
  
  // Safe accessing of recommendation score
  const recommendationScore = (() => {
    try {
      if (typeof summaryData.recommendation_score === 'number') {
        return Math.min(100, Math.max(0, summaryData.recommendation_score));
      }
      return 70; // Default value
    } catch (e) {
      console.error("Error accessing recommendation score:", e);
      return 70;
    }
  })();
  
  // Helper function to determine color based on score
  const getRecommendationColor = (score: number) => {
    if (score > 80) return colors.strengths;
    if (score > 60) return colors.recommendation;
    if (score > 40) return theme.palette.warning.light;
    return colors.improvements;
  };
  
  // Safe accessing of text fields
  const candidateName = summaryData.candidate_name ?? 'Candidate';
  const position = summaryData.position ?? 'Position';
  const recommendationText = summaryData.recommendation_text ?? 'Candidate shows potential for the role.';
  
  return (
    <Box sx={{ mt: 2 }}>
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Interview Analysis Dashboard
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Visual summary of {candidateName}'s interview for the {position} position.
        </Typography>
        
        <Grid container spacing={4}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                Technical Skills Assessment
              </Typography>
              <Box sx={{ height: 300 }}>
                {processedSkills.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart 
                      outerRadius={90} 
                      data={processedSkills}
                      cy="50%"
                    >
                      <PolarGrid strokeDasharray="3 3" />
                      <PolarAngleAxis 
                        dataKey="subject" 
                        tick={{ fontSize: 12, fill: theme.palette.text.primary }}
                        tickFormatter={(value) => {
                          // Make sure skill names aren't too long
                          return value.length > 12 ? value.substring(0, 10) + '...' : value;
                        }}
                      />
                      <PolarRadiusAxis 
                        domain={[0, 100]} 
                        axisLine={false}
                        tick={{ fontSize: 10 }}
                      />
                      <Radar 
                        name="Skill Level" 
                        dataKey="score" 
                        stroke={colors.skills} 
                        fill={colors.skills} 
                        fillOpacity={0.6}
                        isAnimationActive={true}
                        animationDuration={1000}
                        animationEasing="ease-in-out"
                      />
                      <Tooltip 
                        formatter={(value) => [`${value}/100`, 'Skill Level']}
                      />
                      <Legend iconType="circle" />
                    </RadarChart>
                  </ResponsiveContainer>
                ) : (
                  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                    <Typography variant="body1" color="text.secondary">
                      No skill data available
                    </Typography>
                  </Box>
                )}
              </Box>
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                Strengths & Areas for Growth
              </Typography>
              <Box sx={{ height: 300 }}>
                {strengthsAndImprovements.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={strengthsAndImprovements}
                      layout="vertical"
                      margin={{ top: 5, right: 30, left: 120, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" domain={[0, 100]} />
                      <YAxis 
                        type="category" 
                        dataKey="name" 
                        width={120}
                        tick={{ fontSize: 12 }}
                        tickFormatter={(value) => {
                          // Make sure tick values aren't too long
                          return value.length > 15 ? value.substring(0, 12) + '...' : value;
                        }}
                      />
                      <Tooltip 
                        formatter={(value, _, props) => {
                          // Format the tooltip text
                          return [`${value}`, props.payload.type === 'Strength' ? 'Strength' : 'Area for Improvement'];
                        }}
                      />
                      <Legend />
                      <Bar 
                        dataKey="value" 
                        name="Score"
                        radius={[0, 4, 4, 0]} // Rounded corners on right side
                        animationDuration={1000}
                      >
                        {strengthsAndImprovements.map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={entry.type === 'Strength' ? colors.strengths : colors.improvements} 
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                    <Typography variant="body1" color="text.secondary">
                      No strengths or improvements data available
                    </Typography>
                  </Box>
                )}
              </Box>
            </Paper>
          </Grid>
        </Grid>
        
        <Paper sx={{ p: 2, mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Overall Recommendation
          </Typography>
          <Box sx={{ mb: 2 }}>
            <Box sx={{ 
              width: '100%', 
              height: 20, 
              backgroundColor: theme.palette.grey[200],
              borderRadius: 4,
              overflow: 'hidden',
              boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.1)'
            }}>
              <Box sx={{ 
                height: '100%', 
                width: `${recommendationScore}%`,
                backgroundColor: getRecommendationColor(recommendationScore),
                transition: 'width 1.5s cubic-bezier(0.4, 0, 0.2, 1)',
                borderRadius: '4px 0 0 4px'
              }} />
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1, px: 1 }}>
              <Typography variant="body2" color="text.secondary">Not Recommended</Typography>
              <Typography variant="body2" fontWeight="bold" sx={{ 
                color: getRecommendationColor(recommendationScore),
                animation: 'fadeIn 1s ease-in-out'
              }}>
                {recommendationScore}%
              </Typography>
              <Typography variant="body2" color="text.secondary">Highly Recommended</Typography>
            </Box>
          </Box>
          <Typography variant="body1" sx={{ 
            mt: 2, 
            fontStyle: 'italic',
            px: 1,
            pb: 1,
            borderLeft: `4px solid ${getRecommendationColor(recommendationScore)}`,
            backgroundColor: theme.palette.background.default,
            borderRadius: '0 4px 4px 0'
          }}>
            "{recommendationText}"
          </Typography>
        </Paper>
      </Paper>
    </Box>
  );
};

export default InterviewSummaryVisual; 