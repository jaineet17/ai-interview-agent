import React from 'react';
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  ResponsiveContainer, Cell
} from 'recharts';
import { Box, Typography, Paper, Grid, useTheme } from '@mui/material';

interface SkillRating {
  name: string;
  score: number;
}

interface StrengthOrImprovement {
  text: string;
  score: number;
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
  
  // Prepare skill data for radar chart
  const skillData = summaryData.skill_ratings.map(skill => ({
    subject: skill.name,
    score: skill.score,
    fullMark: 100
  }));
  
  // Colors for the visual elements
  const colors = {
    skills: theme.palette.primary.main,
    strengths: theme.palette.success.main,
    improvements: theme.palette.error.main,
    recommendation: theme.palette.warning.main
  };

  // Prepare data for strengths and improvements chart
  const strengthsAndImprovements = [
    ...summaryData.strengths.map(s => ({ name: s.text, value: s.score, type: 'Strength' })),
    ...summaryData.improvements.map(i => ({ name: i.text, value: i.score, type: 'Improvement' }))
  ];

  const getRecommendationColor = (score: number) => {
    if (score > 80) return colors.strengths;
    if (score > 60) return colors.recommendation;
    if (score > 40) return theme.palette.warning.light;
    return colors.improvements;
  };
  
  return (
    <Box sx={{ mt: 2 }}>
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Interview Analysis Dashboard
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Visual summary of {summaryData.candidate_name}'s interview for the {summaryData.position} position.
        </Typography>
        
        <Grid container spacing={4}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                Technical Skills Assessment
              </Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart outerRadius={90} data={skillData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="subject" />
                    <PolarRadiusAxis domain={[0, 100]} />
                    <Radar 
                      name="Skill Level" 
                      dataKey="score" 
                      stroke={colors.skills} 
                      fill={colors.skills} 
                      fillOpacity={0.6} 
                    />
                    <Tooltip />
                    <Legend />
                  </RadarChart>
                </ResponsiveContainer>
              </Box>
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                Strengths & Areas for Growth
              </Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={strengthsAndImprovements}
                    layout="vertical"
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" domain={[0, 100]} />
                    <YAxis type="category" dataKey="name" width={150} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="value" name="Score">
                      {strengthsAndImprovements.map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={entry.type === 'Strength' ? colors.strengths : colors.improvements} 
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
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
              backgroundColor: theme.palette.grey[300],
              borderRadius: 1,
              overflow: 'hidden'
            }}>
              <Box sx={{ 
                height: '100%', 
                width: `${summaryData.recommendation_score}%`,
                backgroundColor: getRecommendationColor(summaryData.recommendation_score),
                transition: 'width 1s ease-in-out'
              }} />
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
              <Typography variant="caption">Not Recommended</Typography>
              <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                {summaryData.recommendation_score}%
              </Typography>
              <Typography variant="caption">Highly Recommended</Typography>
            </Box>
          </Box>
          <Typography variant="body1" sx={{ mt: 2, fontStyle: 'italic' }}>
            "{summaryData.recommendation_text}"
          </Typography>
        </Paper>
      </Paper>
    </Box>
  );
};

export default InterviewSummaryVisual; 