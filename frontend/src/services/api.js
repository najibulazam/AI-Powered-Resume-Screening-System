import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health check
export const healthCheck = () => api.get('/health');

// Upload endpoints
export const uploadJobDescription = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/api/upload/job-description', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const uploadResumes = (files) => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  return api.post('/api/upload/resumes', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

// Parsing endpoints
export const parseJobDescription = (fileId) => 
  api.get(`/api/parse/job-description/${fileId}`);

export const parseResume = (fileId) => 
  api.get(`/api/parse/resume/${fileId}`);

export const parseResumesBatch = (fileIds) => 
  api.post('/api/parse/resumes/batch', fileIds);

// AI Agent endpoints
export const parseResumeWithAI = (text) => 
  api.post('/api/agents/parse-resume', { text });

export const parseResumeFromFile = (fileId) => 
  api.post(`/api/agents/parse-resume-from-file?file_id=${fileId}`);

export const analyzeJobDescription = (text) => 
  api.post('/api/agents/analyze-job-description', { text });

export const analyzeJobFromFile = (fileId) => 
  api.post(`/api/agents/analyze-job-from-file?file_id=${fileId}`);

export const matchCandidate = (resumeFileId, jobFileId) => 
  api.post(`/api/agents/match-candidate?resume_file_id=${resumeFileId}&job_file_id=${jobFileId}`);

// Scoring endpoints
export const scoreCandidate = (data) => 
  api.post('/api/agents/score-candidate', data);

// Feedback endpoints
export const generateFeedback = (data) => 
  api.post('/api/agents/generate-feedback', data);

// Orchestration endpoints
export const screenSingleCandidate = (data) => 
  api.post('/api/screen/process', data);

export const screenBatchCandidates = (data) => 
  api.post('/api/screen/batch', data);

export const checkBatchStatus = (batchId) => 
  api.post('/api/screen/batch/status', { batch_id: batchId });

// Analytics endpoints
export const getDashboardAnalytics = (timeRange = 'all_time') => 
  api.get(`/api/analytics/dashboard?time_range=${timeRange}`);

export const analyzeSkillGaps = (data) => 
  api.post('/api/analytics/skills', data);

export const analyzeCosts = (data) => 
  api.post('/api/analytics/costs', data);

// Export endpoints
export const exportResults = (data) => 
  api.post('/api/export', data);

export default api;
