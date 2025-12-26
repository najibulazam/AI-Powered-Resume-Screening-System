import React, { useState } from 'react';
import {
  parseResumeWithAI,
  analyzeJobDescription,
  matchCandidate,
  generateFeedback
} from '../services/api';

function AgentsPage() {
  const [activeTab, setActiveTab] = useState('resume-parser');
  const [resumeText, setResumeText] = useState('');
  const [jobText, setJobText] = useState('');
  const [resumeFileId, setResumeFileId] = useState('');
  const [jobFileId, setJobFileId] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleParseResume = async () => {
    if (!resumeText.trim()) {
      setError('Please enter resume text');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await parseResumeWithAI(resumeText);
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to parse resume');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeJob = async () => {
    if (!jobText.trim()) {
      setError('Please enter job description text');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await analyzeJobDescription(jobText);
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze job');
    } finally {
      setLoading(false);
    }
  };

  const handleMatchCandidate = async () => {
    if (!resumeFileId || !jobFileId) {
      setError('Please provide both file IDs');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await matchCandidate(resumeFileId, jobFileId);
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to match candidate');
    } finally {
      setLoading(false);
    }
  };

  const renderAgentInfo = () => {
    const agentInfo = {
      'resume-parser': {
        icon: 'bi-file-person',
        color: 'primary',
        title: 'Resume Parser Agent',
        description: 'Extracts structured data from resume text using AI',
        features: [
          'Extracts contact information',
          'Identifies skills and technologies',
          'Parses work experience',
          'Extracts education details',
          'Validates data structure'
        ]
      },
      'job-analyzer': {
        icon: 'bi-briefcase',
        color: 'success',
        title: 'Job Analyzer Agent',
        description: 'Analyzes job descriptions and extracts requirements',
        features: [
          'Identifies required vs preferred skills',
          'Determines experience level',
          'Extracts job responsibilities',
          'Identifies key qualifications',
          'Categorizes job attributes'
        ]
      },
      'skill-matcher': {
        icon: 'bi-diagram-3',
        color: 'info',
        title: 'Skill Matcher Agent',
        description: 'Compares candidate skills against job requirements',
        features: [
          'Calculates skill match percentage',
          'Identifies missing required skills',
          'Finds skill gaps',
          'Provides match recommendations',
          'Generates match level (weak/good/strong/excellent)'
        ]
      },
      'feedback': {
        icon: 'bi-chat-left-text',
        color: 'warning',
        title: 'Feedback Generator Agent',
        description: 'Creates personalized candidate feedback',
        features: [
          'Generates personalized feedback',
          'Highlights strengths',
          'Identifies improvement areas',
          'Provides learning recommendations',
          'Adjusts tone based on decision'
        ]
      }
    };

    const info = agentInfo[activeTab];

    return (
      <div className={`card border-${info.color} mb-4`}>
        <div className={`card-header bg-${info.color} text-white`}>
          <h5 className="mb-0">
            <i className={`bi ${info.icon} me-2`}></i>
            {info.title}
          </h5>
        </div>
        <div className="card-body">
          <p className="lead">{info.description}</p>
          <h6 className="mt-3 mb-2">Key Features:</h6>
          <ul>
            {info.features.map((feature, index) => (
              <li key={index}>{feature}</li>
            ))}
          </ul>
        </div>
      </div>
    );
  };

  return (
    <div className="container">
      <div className="row">
        <div className="col-12">
          <h1 className="mb-4">
            <i className="bi bi-cpu text-primary me-2"></i>
            AI Agents Playground
          </h1>
          <p className="text-muted mb-5">
            Test individual AI agents and see how they process data
          </p>
        </div>
      </div>

      {/* Agent Tabs */}
      <ul className="nav nav-pills mb-4" role="tablist">
        <li className="nav-item" role="presentation">
          <button
            className={`nav-link ${activeTab === 'resume-parser' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('resume-parser');
              setResult(null);
              setError(null);
            }}
          >
            <i className="bi bi-file-person me-2"></i>
            Resume Parser
          </button>
        </li>
        <li className="nav-item" role="presentation">
          <button
            className={`nav-link ${activeTab === 'job-analyzer' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('job-analyzer');
              setResult(null);
              setError(null);
            }}
          >
            <i className="bi bi-briefcase me-2"></i>
            Job Analyzer
          </button>
        </li>
        <li className="nav-item" role="presentation">
          <button
            className={`nav-link ${activeTab === 'skill-matcher' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('skill-matcher');
              setResult(null);
              setError(null);
            }}
          >
            <i className="bi bi-diagram-3 me-2"></i>
            Skill Matcher
          </button>
        </li>
        <li className="nav-item" role="presentation">
          <button
            className={`nav-link ${activeTab === 'feedback' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('feedback');
              setResult(null);
              setError(null);
            }}
          >
            <i className="bi bi-chat-left-text me-2"></i>
            Feedback Generator
          </button>
        </li>
      </ul>

      {error && (
        <div className="alert alert-danger alert-dismissible fade show" role="alert">
          <i className="bi bi-exclamation-triangle me-2"></i>
          {error}
          <button 
            type="button" 
            className="btn-close" 
            onClick={() => setError(null)}
          ></button>
        </div>
      )}

      {renderAgentInfo()}

      {/* Resume Parser Tab */}
      {activeTab === 'resume-parser' && (
        <div className="row">
          <div className="col-lg-6">
            <div className="card shadow-sm">
              <div className="card-header">
                <h5 className="mb-0">Input</h5>
              </div>
              <div className="card-body">
                <label className="form-label">Resume Text</label>
                <textarea
                  className="form-control"
                  rows="15"
                  value={resumeText}
                  onChange={(e) => setResumeText(e.target.value)}
                  placeholder="Paste resume text here...&#10;&#10;John Doe&#10;john@example.com&#10;&#10;Experience:&#10;Senior Software Engineer at Tech Corp&#10;2020-Present&#10;..."
                  disabled={loading}
                />
                <button
                  className="btn btn-primary w-100 mt-3"
                  onClick={handleParseResume}
                  disabled={loading || !resumeText}
                >
                  {loading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2"></span>
                      Processing...
                    </>
                  ) : (
                    <>
                      <i className="bi bi-play-circle me-2"></i>
                      Parse Resume
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
          <div className="col-lg-6">
            <div className="card shadow-sm">
              <div className="card-header">
                <h5 className="mb-0">Output</h5>
              </div>
              <div className="card-body">
                {result ? (
                  <pre className="bg-light p-3 rounded" style={{ maxHeight: '500px', overflow: 'auto' }}>
                    {JSON.stringify(result, null, 2)}
                  </pre>
                ) : (
                  <p className="text-muted text-center py-5">
                    Output will appear here after processing
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Job Analyzer Tab */}
      {activeTab === 'job-analyzer' && (
        <div className="row">
          <div className="col-lg-6">
            <div className="card shadow-sm">
              <div className="card-header">
                <h5 className="mb-0">Input</h5>
              </div>
              <div className="card-body">
                <label className="form-label">Job Description Text</label>
                <textarea
                  className="form-control"
                  rows="15"
                  value={jobText}
                  onChange={(e) => setJobText(e.target.value)}
                  placeholder="Paste job description here...&#10;&#10;Senior Software Engineer&#10;&#10;We are seeking a Senior Software Engineer...&#10;&#10;Requirements:&#10;- 5+ years experience&#10;- Python, React, AWS..."
                  disabled={loading}
                />
                <button
                  className="btn btn-success w-100 mt-3"
                  onClick={handleAnalyzeJob}
                  disabled={loading || !jobText}
                >
                  {loading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2"></span>
                      Processing...
                    </>
                  ) : (
                    <>
                      <i className="bi bi-play-circle me-2"></i>
                      Analyze Job
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
          <div className="col-lg-6">
            <div className="card shadow-sm">
              <div className="card-header">
                <h5 className="mb-0">Output</h5>
              </div>
              <div className="card-body">
                {result ? (
                  <pre className="bg-light p-3 rounded" style={{ maxHeight: '500px', overflow: 'auto' }}>
                    {JSON.stringify(result, null, 2)}
                  </pre>
                ) : (
                  <p className="text-muted text-center py-5">
                    Output will appear here after processing
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Skill Matcher Tab */}
      {activeTab === 'skill-matcher' && (
        <div className="row">
          <div className="col-lg-6">
            <div className="card shadow-sm">
              <div className="card-header">
                <h5 className="mb-0">Input</h5>
              </div>
              <div className="card-body">
                <div className="mb-3">
                  <label className="form-label">Resume File ID</label>
                  <input
                    type="text"
                    className="form-control"
                    value={resumeFileId}
                    onChange={(e) => setResumeFileId(e.target.value)}
                    placeholder="resume_20231226_abc123"
                    disabled={loading}
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">Job File ID</label>
                  <input
                    type="text"
                    className="form-control"
                    value={jobFileId}
                    onChange={(e) => setJobFileId(e.target.value)}
                    placeholder="jd_20231226_xyz789"
                    disabled={loading}
                  />
                </div>
                <button
                  className="btn btn-info w-100"
                  onClick={handleMatchCandidate}
                  disabled={loading || !resumeFileId || !jobFileId}
                >
                  {loading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2"></span>
                      Processing...
                    </>
                  ) : (
                    <>
                      <i className="bi bi-play-circle me-2"></i>
                      Match Candidate
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
          <div className="col-lg-6">
            <div className="card shadow-sm">
              <div className="card-header">
                <h5 className="mb-0">Output</h5>
              </div>
              <div className="card-body">
                {result ? (
                  <pre className="bg-light p-3 rounded" style={{ maxHeight: '500px', overflow: 'auto' }}>
                    {JSON.stringify(result, null, 2)}
                  </pre>
                ) : (
                  <p className="text-muted text-center py-5">
                    Output will appear here after processing
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Feedback Generator Tab */}
      {activeTab === 'feedback' && (
        <div className="row">
          <div className="col-12">
            <div className="alert alert-info">
              <i className="bi bi-info-circle me-2"></i>
              The Feedback Generator is part of the complete screening pipeline. 
              Use the <strong>Screening</strong> page with "Generate Feedback" enabled to see this agent in action.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AgentsPage;
