import React, { useState, useEffect } from 'react';
import { screenBatchCandidates, checkBatchStatus } from '../services/api';

function BatchScreeningPage() {
  const [jobFileId, setJobFileId] = useState('');
  const [resumeFileIds, setResumeFileIds] = useState('');
  const [includeFeedback, setIncludeFeedback] = useState(false);
  const [hireThreshold, setHireThreshold] = useState(75);
  const [rejectThreshold, setRejectThreshold] = useState(50);
  const [loading, setLoading] = useState(false);
  const [batchId, setBatchId] = useState(null);
  const [batchStatus, setBatchStatus] = useState(null);
  const [error, setError] = useState(null);
  const [pollInterval, setPollInterval] = useState(null);

  useEffect(() => {
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [pollInterval]);

  const handleStartBatch = async () => {
    if (!jobFileId || !resumeFileIds) {
      setError('Please provide Job File ID and at least one Resume File ID');
      return;
    }

    // Parse resume file IDs (comma or newline separated)
    const fileIdArray = resumeFileIds
      .split(/[,\n]/)
      .map(id => id.trim())
      .filter(id => id.length > 0);

    if (fileIdArray.length === 0) {
      setError('Please provide at least one valid Resume File ID');
      return;
    }

    setLoading(true);
    setError(null);
    setBatchStatus(null);

    try {
      const response = await screenBatchCandidates({
        job_file_id: jobFileId,
        resume_file_ids: fileIdArray,
        include_feedback: includeFeedback,
        include_score_in_feedback: false,
        custom_thresholds: {
          hire: parseFloat(hireThreshold),
          reject: parseFloat(rejectThreshold)
        }
      });

      if (response.data.success) {
        setBatchId(response.data.batch_id);
        // Start polling for status
        startPolling(response.data.batch_id);
      } else {
        setError(response.data.error || 'Failed to start batch screening');
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to start batch screening');
    } finally {
      setLoading(false);
    }
  };

  const startPolling = (id) => {
    // Poll every 2 seconds
    const interval = setInterval(async () => {
      try {
        const response = await checkBatchStatus(id);
        if (response.data.success) {
          setBatchStatus(response.data);
          
          // Stop polling if complete
          if (response.data.progress_percent >= 100) {
            clearInterval(interval);
            setPollInterval(null);
          }
        }
      } catch (err) {
        console.error('Failed to check batch status:', err);
      }
    }, 2000);

    setPollInterval(interval);
  };

  const handleRefreshStatus = async () => {
    if (!batchId) return;

    try {
      const response = await checkBatchStatus(batchId);
      if (response.data.success) {
        setBatchStatus(response.data);
      }
    } catch (err) {
      setError('Failed to refresh status');
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

  return (
    <div className="container">
      <div className="row">
        <div className="col-12">
          <h1 className="mb-4">
            <i className="bi bi-collection text-primary me-2"></i>
            Batch Candidate Screening
          </h1>
          <p className="text-muted mb-5">
            Process multiple candidates simultaneously for the same job posting
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
                Batch Configuration
              </h5>
            </div>
            <div className="card-body">
              <div className="mb-3">
                <label className="form-label">Job Description File ID</label>
                <input
                  type="text"
                  className="form-control"
                  value={jobFileId}
                  onChange={(e) => setJobFileId(e.target.value)}
                  placeholder="jd_20231226_xyz789"
                  disabled={loading || batchId}
                />
              </div>

              <div className="mb-3">
                <label className="form-label">Resume File IDs (one per line or comma-separated)</label>
                <textarea
                  className="form-control"
                  rows="6"
                  value={resumeFileIds}
                  onChange={(e) => setResumeFileIds(e.target.value)}
                  placeholder="resume_001&#10;resume_002&#10;resume_003"
                  disabled={loading || batchId}
                />
                <small className="text-muted">
                  Max 100 candidates per batch
                </small>
              </div>

              <hr />

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
                  disabled={loading || batchId}
                />
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
                  disabled={loading || batchId}
                />
              </div>

              <div className="form-check mb-3">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="batchIncludeFeedback"
                  checked={includeFeedback}
                  onChange={(e) => setIncludeFeedback(e.target.checked)}
                  disabled={loading || batchId}
                />
                <label className="form-check-label" htmlFor="batchIncludeFeedback">
                  Generate Feedback (increases processing time)
                </label>
              </div>

              {!batchId ? (
                <button
                  className="btn btn-primary w-100"
                  onClick={handleStartBatch}
                  disabled={loading || !jobFileId || !resumeFileIds}
                >
                  {loading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2"></span>
                      Starting...
                    </>
                  ) : (
                    <>
                      <i className="bi bi-play-circle me-2"></i>
                      Start Batch Processing
                    </>
                  )}
                </button>
              ) : (
                <button
                  className="btn btn-secondary w-100"
                  onClick={() => {
                    setBatchId(null);
                    setBatchStatus(null);
                    if (pollInterval) {
                      clearInterval(pollInterval);
                      setPollInterval(null);
                    }
                  }}
                >
                  <i className="bi bi-arrow-clockwise me-2"></i>
                  New Batch
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="col-lg-8">
          {batchStatus && (
            <div className="fade-in">
              {/* Progress Card */}
              <div className="card shadow-sm mb-4">
                <div className="card-header bg-dark text-white">
                  <div className="d-flex justify-content-between align-items-center">
                    <h5 className="mb-0">
                      <i className="bi bi-hourglass-split me-2"></i>
                      Batch Progress
                    </h5>
                    <button
                      className="btn btn-sm btn-light"
                      onClick={handleRefreshStatus}
                    >
                      <i className="bi bi-arrow-clockwise"></i>
                    </button>
                  </div>
                </div>
                <div className="card-body">
                  <div className="mb-3">
                    <div className="d-flex justify-content-between mb-2">
                      <span>Progress</span>
                      <span className="fw-bold">{batchStatus.progress_percent.toFixed(1)}%</span>
                    </div>
                    <div className="progress progress-custom">
                      <div
                        className="progress-bar progress-bar-striped progress-bar-animated"
                        role="progressbar"
                        style={{ width: `${batchStatus.progress_percent}%` }}
                      >
                        {batchStatus.completed_jobs} / {batchStatus.total_jobs}
                      </div>
                    </div>
                  </div>

                  <div className="row g-3">
                    <div className="col-md-3">
                      <div className="card stat-card stat-primary">
                        <div className="card-body text-center">
                          <h6 className="text-muted small mb-1">Total</h6>
                          <h4 className="mb-0">{batchStatus.total_jobs}</h4>
                        </div>
                      </div>
                    </div>
                    <div className="col-md-3">
                      <div className="card stat-card stat-success">
                        <div className="card-body text-center">
                          <h6 className="text-muted small mb-1">Completed</h6>
                          <h4 className="mb-0">{batchStatus.completed_jobs}</h4>
                        </div>
                      </div>
                    </div>
                    <div className="col-md-3">
                      <div className="card stat-card stat-warning">
                        <div className="card-body text-center">
                          <h6 className="text-muted small mb-1">Pending</h6>
                          <h4 className="mb-0">{batchStatus.pending_jobs}</h4>
                        </div>
                      </div>
                    </div>
                    <div className="col-md-3">
                      <div className="card stat-card stat-danger">
                        <div className="card-body text-center">
                          <h6 className="text-muted small mb-1">Failed</h6>
                          <h4 className="mb-0">{batchStatus.failed_jobs}</h4>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Decision Summary */}
              {batchStatus.decisions_summary && (
                <div className="card shadow-sm mb-4">
                  <div className="card-header">
                    <h5 className="mb-0">
                      <i className="bi bi-pie-chart me-2"></i>
                      Decision Summary
                    </h5>
                  </div>
                  <div className="card-body">
                    <div className="row g-3">
                      <div className="col-md-4">
                        <div className="card border-success">
                          <div className="card-body text-center">
                            <h6 className="text-success">
                              <i className="bi bi-check-circle me-1"></i>
                              HIRE
                            </h6>
                            <h2 className="mb-0 text-success">
                              {batchStatus.decisions_summary.HIRE || 0}
                            </h2>
                          </div>
                        </div>
                      </div>
                      <div className="col-md-4">
                        <div className="card border-warning">
                          <div className="card-body text-center">
                            <h6 className="text-warning">
                              <i className="bi bi-dash-circle me-1"></i>
                              MAYBE
                            </h6>
                            <h2 className="mb-0 text-warning">
                              {batchStatus.decisions_summary.MAYBE || 0}
                            </h2>
                          </div>
                        </div>
                      </div>
                      <div className="col-md-4">
                        <div className="card border-danger">
                          <div className="card-body text-center">
                            <h6 className="text-danger">
                              <i className="bi bi-x-circle me-1"></i>
                              REJECT
                            </h6>
                            <h2 className="mb-0 text-danger">
                              {batchStatus.decisions_summary.REJECT || 0}
                            </h2>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Results Table */}
              {batchStatus.results && batchStatus.results.length > 0 && (
                <div className="card shadow-sm">
                  <div className="card-header">
                    <h5 className="mb-0">
                      <i className="bi bi-table me-2"></i>
                      Screening Results
                    </h5>
                  </div>
                  <div className="card-body">
                    <div className="table-responsive">
                      <table className="table table-hover">
                        <thead>
                          <tr>
                            <th>#</th>
                            <th>Decision</th>
                            <th>Score</th>
                            <th>Match %</th>
                            <th>Match Level</th>
                            <th>Confidence</th>
                          </tr>
                        </thead>
                        <tbody>
                          {batchStatus.results.map((result, index) => (
                            <tr key={index}>
                              <td>{index + 1}</td>
                              <td>
                                <span className={`badge ${getDecisionBadgeClass(result.decision)}`}>
                                  {result.decision}
                                </span>
                              </td>
                              <td className="fw-bold">{result.overall_score?.toFixed(1)}</td>
                              <td>{result.required_skills_match_percent?.toFixed(1)}%</td>
                              <td className="text-capitalize">{result.match_level}</td>
                              <td>{result.confidence_level?.toFixed(1)}%</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {!batchStatus && !loading && (
            <div className="card shadow-sm">
              <div className="card-body text-center py-5 text-muted">
                <i className="bi bi-arrow-left" style={{ fontSize: '3rem' }}></i>
                <p className="mt-3 mb-0">
                  Configure batch parameters and click "Start Batch Processing"
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default BatchScreeningPage;
