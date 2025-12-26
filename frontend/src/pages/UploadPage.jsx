import React, { useState } from 'react';
import { uploadJobDescription, uploadResumes } from '../services/api';

function UploadPage() {
  const [jobFile, setJobFile] = useState(null);
  const [resumeFiles, setResumeFiles] = useState([]);
  const [jobUploadResult, setJobUploadResult] = useState(null);
  const [resumeUploadResult, setResumeUploadResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleJobFileChange = (e) => {
    setJobFile(e.target.files[0]);
    setJobUploadResult(null);
    setError(null);
  };

  const handleResumeFilesChange = (e) => {
    setResumeFiles(Array.from(e.target.files));
    setResumeUploadResult(null);
    setError(null);
  };

  const handleJobUpload = async () => {
    if (!jobFile) {
      setError('Please select a job description file');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await uploadJobDescription(jobFile);
      setJobUploadResult(response.data);
      setJobFile(null);
      // Clear file input
      document.getElementById('jobFileInput').value = '';
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload job description');
    } finally {
      setLoading(false);
    }
  };

  const handleResumeUpload = async () => {
    if (resumeFiles.length === 0) {
      setError('Please select at least one resume file');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await uploadResumes(resumeFiles);
      setResumeUploadResult(response.data);
      setResumeFiles([]);
      // Clear file input
      document.getElementById('resumeFileInput').value = '';
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload resumes');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="row">
        <div className="col-12">
          <h1 className="mb-4">
            <i className="bi bi-cloud-upload text-primary me-2"></i>
            Upload Files
          </h1>
          <p className="text-muted mb-5">
            Upload job descriptions and resumes to start the screening process
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

      <div className="row g-4">
        {/* Job Description Upload */}
        <div className="col-lg-6">
          <div className="card shadow-sm h-100">
            <div className="card-header bg-primary text-white">
              <h5 className="mb-0">
                <i className="bi bi-file-text me-2"></i>
                Job Description
              </h5>
            </div>
            <div className="card-body">
              <div className="mb-4">
                <label htmlFor="jobFileInput" className="form-label">
                  Select Job Description (PDF or TXT)
                </label>
                <input
                  type="file"
                  className="form-control"
                  id="jobFileInput"
                  accept=".pdf,.txt"
                  onChange={handleJobFileChange}
                  disabled={loading}
                />
                {jobFile && (
                  <div className="mt-2">
                    <small className="text-muted">
                      <i className="bi bi-file-earmark me-1"></i>
                      {jobFile.name} ({(jobFile.size / 1024).toFixed(2)} KB)
                    </small>
                  </div>
                )}
              </div>

              <button
                className="btn btn-primary w-100"
                onClick={handleJobUpload}
                disabled={!jobFile || loading}
              >
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2"></span>
                    Uploading...
                  </>
                ) : (
                  <>
                    <i className="bi bi-upload me-2"></i>
                    Upload Job Description
                  </>
                )}
              </button>

              {jobUploadResult && (
                <div className="alert alert-success mt-4" role="alert">
                  <h6 className="alert-heading">
                    <i className="bi bi-check-circle me-2"></i>
                    Upload Successful!
                  </h6>
                  <hr />
                  <p className="mb-1">
                    <strong>File ID:</strong> 
                    <code className="ms-2">{jobUploadResult.file_id}</code>
                  </p>
                  <p className="mb-1">
                    <strong>Filename:</strong> {jobUploadResult.filename}
                  </p>
                  <p className="mb-0">
                    <strong>Size:</strong> {(jobUploadResult.file_size / 1024).toFixed(2)} KB
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Resume Upload */}
        <div className="col-lg-6">
          <div className="card shadow-sm h-100">
            <div className="card-header bg-success text-white">
              <h5 className="mb-0">
                <i className="bi bi-person-badge me-2"></i>
                Resumes
              </h5>
            </div>
            <div className="card-body">
              <div className="mb-4">
                <label htmlFor="resumeFileInput" className="form-label">
                  Select Resume Files (PDF or TXT, multiple allowed)
                </label>
                <input
                  type="file"
                  className="form-control"
                  id="resumeFileInput"
                  accept=".pdf,.txt"
                  multiple
                  onChange={handleResumeFilesChange}
                  disabled={loading}
                />
                {resumeFiles.length > 0 && (
                  <div className="mt-2">
                    <small className="text-muted">
                      <i className="bi bi-files me-1"></i>
                      {resumeFiles.length} file(s) selected
                    </small>
                    <ul className="list-unstyled mt-2">
                      {resumeFiles.map((file, index) => (
                        <li key={index} className="text-muted small">
                          <i className="bi bi-file-earmark me-1"></i>
                          {file.name} ({(file.size / 1024).toFixed(2)} KB)
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              <button
                className="btn btn-success w-100"
                onClick={handleResumeUpload}
                disabled={resumeFiles.length === 0 || loading}
              >
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2"></span>
                    Uploading...
                  </>
                ) : (
                  <>
                    <i className="bi bi-upload me-2"></i>
                    Upload Resumes
                  </>
                )}
              </button>

              {resumeUploadResult && (
                <div className="alert alert-success mt-4" role="alert">
                  <h6 className="alert-heading">
                    <i className="bi bi-check-circle me-2"></i>
                    Upload Successful!
                  </h6>
                  <hr />
                  <p className="mb-1">
                    <strong>Total Files:</strong> {resumeUploadResult.total_files}
                  </p>
                  <p className="mb-2">
                    <strong>File IDs:</strong>
                  </p>
                  <div className="file-ids-container" style={{ maxHeight: '200px', overflowY: 'auto' }}>
                    {resumeUploadResult.file_ids.map((id, index) => (
                      <div key={index} className="mb-1">
                        <code className="small">{id}</code>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Instructions */}
      <div className="row mt-5">
        <div className="col-12">
          <div className="card border-info">
            <div className="card-header bg-info text-white">
              <h5 className="mb-0">
                <i className="bi bi-info-circle me-2"></i>
                Next Steps
              </h5>
            </div>
            <div className="card-body">
              <ol className="mb-0">
                <li className="mb-2">
                  Upload a job description and one or more resumes using the forms above
                </li>
                <li className="mb-2">
                  Copy the File IDs from the upload results
                </li>
                <li className="mb-2">
                  Go to the <strong>Screening</strong> page to process individual candidates
                </li>
                <li className="mb-0">
                  Or use <strong>Batch Processing</strong> to screen multiple candidates at once
                </li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default UploadPage;
