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
  
  // CRITICAL FIX: Clean and validate skill data
  const safeSkillData = React.useMemo(() => {
    if (!summaryData?.skill_ratings || !Array.isArray(summaryData.skill_ratings)) {
      return [];
    }
    
    return summaryData.skill_ratings
      .filter(item => 
        item && 
        typeof item === 'object' && 
        typeof item.name === 'string' && 
        typeof item.score === 'number'
      )
      .map(skill => ({
        subject: skill.name,
        score: Math.max(0, Math.min(100, skill.score)), // Ensure score is between 0 and 100
        fullMark: 100
      }));
  }, [summaryData?.skill_ratings]);
  
  // CRITICAL FIX: Clean and validate strengths and improvements
  const safeStrengthsAndImprovements = React.useMemo(() => {
    const strengths = summaryData?.strengths || [];
    const improvements = summaryData?.improvements || [];
    
    const processItems = (items: StrengthOrImprovement[], type: 'Strength' | 'Improvement') => {
      return items
        .filter(item => 
          item && 
          typeof item === 'object' && 
          typeof item.text === 'string' && 
          typeof item.score === 'number'
        )
        .map(item => ({
          name: item.text,
          value: Math.max(0, Math.min(100, item.score)), // Ensure score is between 0 and 100
          type
        }));
    };
    
    return [
      ...processItems(strengths, 'Strength'),
      ...processItems(improvements, 'Improvement')
    ];
  }, [summaryData?.strengths, summaryData?.improvements]);
  
  // Colors for the visual elements
  const colors = {
    skills: theme.palette.primary.main,
    strengths: theme.palette.success.main,
    improvements: theme.palette.error.main,
    recommendation: theme.palette.warning.main
  };

  const getRecommendationColor = (score: number) => {
    if (score > 80) return colors.strengths;
    if (score > 60) return colors.recommendation;
    if (score > 40) return theme.palette.warning.light;
    return colors.improvements;
  };
  
  // CRITICAL FIX: Ensure recommendation score is valid
  const safeRecommendationScore = Math.max(0, Math.min(100, summaryData?.recommendation_score || 50));
  
  return (
    <Box sx={{ mt: 2 }}>
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Interview Analysis Dashboard
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Visual summary of {summaryData?.candidate_name || 'Candidate'}'s interview for the {summaryData?.position || 'Position'} position.
        </Typography>
        
        <Grid container spacing={4}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                Technical Skills Assessment
              </Typography>
              <Box sx={{ height: 300 }}>
                {safeSkillData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart outerRadius={90} data={safeSkillData}>
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
                ) : (
                  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                    <Typography variant="body2" color="text.secondary">
                      Skill data not available
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
                {safeStrengthsAndImprovements.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={safeStrengthsAndImprovements}
                      layout="vertical"
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" domain={[0, 100]} />
                      <YAxis type="category" dataKey="name" width={150} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="value" name="Score">
                        {safeStrengthsAndImprovements.map((entry, index) => (
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
                    <Typography variant="body2" color="text.secondary">
                      Strengths and improvements data not available
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
              backgroundColor: theme.palette.grey[300],
              borderRadius: 1,
              overflow: 'hidden'
            }}>
              <Box sx={{ 
                height: '100%', 
                width: `${safeRecommendationScore}%`,
                backgroundColor: getRecommendationColor(safeRecommendationScore),
                transition: 'width 1s ease-in-out'
              }} />
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
              <Typography variant="caption">Not Recommended</Typography>
              <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                {safeRecommendationScore}%
              </Typography>
              <Typography variant="caption">Highly Recommended</Typography>
            </Box>
          </Box>
          <Typography variant="body1" sx={{ mt: 2, fontStyle: 'italic' }}>
            "{summaryData?.recommendation_text || 'Additional assessment recommended'}"
          </Typography>
        </Paper>
      </Paper>
    </Box>
  );
};

export default InterviewSummaryVisual; 