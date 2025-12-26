import React, { useState } from 'react';
import { screenSingleCandidate } from '../services/api';

function ScreeningPage() {
  const [resumeFileId, setResumeFileId] = useState('');
  const [jobFileId, setJobFileId] = useState('');
  const [includeFeedback, setIncludeFeedback] = useState(true);
  const [includeScoreInFeedback, setIncludeScoreInFeedback] = useState(false);
  const [hireThreshold, setHireThreshold] = useState(75);
  const [rejectThreshold, setRejectThreshold] = useState(50);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleScreen = async () => {
    if (!resumeFileId || !jobFileId) {
      setError('Please provide both Resume File ID and Job File ID');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await screenSingleCandidate({
        resume_file_id: resumeFileId,
        job_file_id: jobFileId,
        include_feedback: includeFeedback,
        include_score_in_feedback: includeScoreInFeedback,
        custom_thresholds: {
          hire: parseFloat(hireThreshold),
          reject: parseFloat(rejectThreshold)
        }
      });

      if (response.data.success) {
        setResult(response.data.result);
      } else {
        setError(response.data.error || 'Screening failed');
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to screen candidate');
    } finally {
      setLoading(false);
    }
  };

  const getDecisionBadgeClass = (decision) => {
    switch (decision?.toUpperCase()) {
      case 'HIRE': return 'badge-hire';
      case 'MAYBE': return 'badge-maybe';
      case 'REJECT': return 'badge-reject';
      default: return 'bg-secondary';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 75) return 'text-success';
    if (score >= 50) return 'text-warning';
    return 'text-danger';
  };

  return (
    <div className="container">
      <div className="row">
        <div className="col-12">
          <h1 className="mb-4">
            <i className="bi bi-search text-primary me-2"></i>
            Single Candidate Screening
          </h1>
          <p className="text-muted mb-5">
            Screen a single candidate through the complete AI pipeline
          </p>
        </div>
      </div>

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

      <div className="row">
        <div className="col-lg-4">
          <div className="card shadow-sm mb-4">
            <div className="card-header bg-primary text-white">
              <h5 className="mb-0">
                <i className="bi bi-sliders me-2"></i>
                Configuration
              </h5>
            </div>
            <div className="card-body">
              {/* File IDs */}
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
                <label className="form-label">Job Description File ID</label>
                <input
                  type="text"
                  className="form-control"
                  value={jobFileId}
                  onChange={(e) => setJobFileId(e.target.value)}
                  placeholder="jd_20231226_xyz789"
                  disabled={loading}
                />
              </div>

              <hr />

              {/* Thresholds */}
              <div className="mb-3">
                <label className="form-label">
                  Hire Threshold: <strong>{hireThreshold}</strong>
                </label>
                <input
                  type="range"
                  className="form-range"
                  min="0"
                  max="100"
                  value={hireThreshold}
                  onChange={(e) => setHireThreshold(e.target.value)}
                  disabled={loading}
                />
                <small className="text-muted">Score ≥ {hireThreshold} = HIRE</small>
              </div>

              <div className="mb-3">
                <label className="form-label">
                  Reject Threshold: <strong>{rejectThreshold}</strong>
                </label>
                <input
                  type="range"
                  className="form-range"
                  min="0"
                  max="100"
                  value={rejectThreshold}
                  onChange={(e) => setRejectThreshold(e.target.value)}
                  disabled={loading}
                />
                <small className="text-muted">Score &lt; {rejectThreshold} = REJECT</small>
              </div>

              <hr />

              {/* Options */}
              <div className="form-check mb-2">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="includeFeedback"
                  checked={includeFeedback}
                  onChange={(e) => setIncludeFeedback(e.target.checked)}
                  disabled={loading}
                />
                <label className="form-check-label" htmlFor="includeFeedback">
                  Generate Feedback
                </label>
              </div>

              <div className="form-check mb-3">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="includeScore"
                  checked={includeScoreInFeedback}
                  onChange={(e) => setIncludeScoreInFeedback(e.target.checked)}
                  disabled={loading || !includeFeedback}
                />
                <label className="form-check-label" htmlFor="includeScore">
                  Include Score in Feedback
                </label>
              </div>

              <button
                className="btn btn-primary w-100"
                onClick={handleScreen}
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
                    Start Screening
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Info Card */}
          <div className="card border-info">
            <div className="card-body">
              <h6 className="card-title">
                <i className="bi bi-info-circle text-info me-2"></i>
                How it works
              </h6>
              <ol className="small mb-0">
                <li>Resume Parser extracts data</li>
                <li>Job Analyzer identifies requirements</li>
                <li>Skill Matcher compares them</li>
                <li>Scorer makes decision</li>
                <li>Feedback Generator creates report</li>
              </ol>
            </div>
          </div>
        </div>

        <div className="col-lg-8">
          {loading && (
            <div className="card shadow-sm">
              <div className="card-body text-center py-5">
                <div className="spinner-border text-primary mb-3" style={{ width: '3rem', height: '3rem' }}>
                  <span className="visually-hidden">Loading...</span>
                </div>
                <h5>Processing candidate...</h5>
                <p className="text-muted">This may take 3-5 seconds</p>
              </div>
            </div>
          )}

          {result && (
            <div className="fade-in">
              {/* Decision Card */}
              <div className="card shadow-sm mb-4">
                <div className="card-header bg-dark text-white">
                  <h5 className="mb-0">
                    <i className="bi bi-clipboard-check me-2"></i>
                    Screening Result
                  </h5>
                </div>
                <div className="card-body text-center py-5">
                  <div className="mb-4">
                    <h2 className="display-5 fw-bold mb-3">
                      <span className={`badge ${getDecisionBadgeClass(result.decision)} fs-1`}>
                        {result.decision}
                      </span>
                    </h2>
                  </div>

                  <div className="row g-4 mb-4">
                    <div className="col-md-4">
                      <div className={`score-display ${getScoreColor(result.overall_score)}`}>
                        {result.overall_score != null ? result.overall_score.toFixed(1) : 'N/A'}
                      </div>
                      <div className="score-label">Overall Score</div>
                    </div>
                    <div className="col-md-4">
                      <div className="score-display text-info">
                        <span className="text-capitalize">{result.confidence || 'N/A'}</span>
                      </div>
                      <div className="score-label">Confidence</div>
                    </div>
                    <div className="col-md-4">
                      <div className="score-display text-info">
                        {result.processing_time_ms?.toFixed(0) || 'N/A'}ms
                      </div>
                      <div className="score-label">Processing Time</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Match Details */}
              <div className="card shadow-sm mb-4">
                <div className="card-header">
                  <h5 className="mb-0">
                    <i className="bi bi-graph-up me-2"></i>
                    Match Analysis
                  </h5>
                </div>
                <div className="card-body">
                  <div className="row g-3 mb-4">
                    <div className="col-md-6">
                      <div className="card stat-card stat-success">
                        <div className="card-body">
                          <h6 className="text-muted mb-2">Matched Skills</h6>
                          <h3 className="mb-0">
                            {result.matched_skills?.length || 0}
                          </h3>
                        </div>
                      </div>
                    </div>
                    <div className="col-md-6">
                      <div className="card stat-card stat-primary">
                        <div className="card-body">
                          <h6 className="text-muted mb-2">Missing Skills</h6>
                          <h3 className="mb-0 text-capitalize">
                            {result.missing_skills?.length || 0}
                          </h3>
                        </div>
                      </div>
                    </div>
                  </div>

                  {result.matched_skills && result.matched_skills.length > 0 && (
                    <div className="mb-4">
                      <h6 className="text-primary mb-3">
                        <i className="bi bi-star me-2"></i>
                        Matched Skills
                      </h6>
                      <div className="d-flex flex-wrap gap-2">
                        {result.matched_skills.map((skill, index) => (
                          <span key={index} className="badge bg-primary">
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {result.strengths && result.strengths.length > 0 && (
                    <div className="mb-4">
                      <h6 className="text-success mb-3">
                        <i className="bi bi-check-circle me-2"></i>
                        Key Strengths
                      </h6>
                      <ul className="list-group">
                        {result.strengths.map((strength, index) => (
                          <li key={index} className="list-group-item">
                            <i className="bi bi-check text-success me-2"></i>
                            {strength}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {result.missing_skills && result.missing_skills.length > 0 && (
                    <div className="mb-4">
                      <h6 className="text-danger mb-3">
                        <i className="bi bi-x-circle me-2"></i>
                        Missing Required Skills
                      </h6>
                      <ul className="list-group">
                        {result.missing_skills.map((skill, index) => (
                          <li key={index} className="list-group-item">
                            <i className="bi bi-x text-danger me-2"></i>
                            {typeof skill === 'string' ? skill : skill.skill_name}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {result.weaknesses && result.weaknesses.length > 0 && (
                    <div>
                      <h6 className="text-info mb-3">
                        <i className="bi bi-lightbulb me-2"></i>
                        Areas for Improvement
                      </h6>
                      <ul className="list-group">
                        {result.weaknesses.map((weakness, index) => (
                          <li key={index} className="list-group-item">
                            <i className="bi bi-arrow-right text-info me-2"></i>
                            {weakness}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              {/* Feedback */}
              {result.feedback_message && (
                <div className="card shadow-sm">
                  <div className="card-header">
                    <h5 className="mb-0">
                      <i className="bi bi-chat-left-text me-2"></i>
                      Candidate Feedback
                    </h5>
                  </div>
                  <div className="card-body">
                    <div className="bg-light p-4 rounded">
                      {result.feedback_message.split('\n').map((line, index) => (
                        <p key={index} className="mb-2">{line}</p>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {!loading && !result && (
            <div className="card shadow-sm">
              <div className="card-body text-center py-5 text-muted">
                <i className="bi bi-arrow-left" style={{ fontSize: '3rem' }}></i>
                <p className="mt-3 mb-0">
                  Configure screening parameters and click "Start Screening"
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ScreeningPage;
