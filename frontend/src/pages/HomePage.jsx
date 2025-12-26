import React from 'react';
import { Link } from 'react-router-dom';

function HomePage() {
  return (
    <div className="container">
      {/* Hero Section */}
      <div className="row align-items-center py-5">
        <div className="col-lg-6">
          <h1 className="display-4 fw-bold mb-4">
            AI-Powered Resume Screening
          </h1>
          <p className="lead text-muted mb-4">
            Automate candidate evaluation with our intelligent multi-agent system. 
            Upload resumes, analyze job requirements, and get instant hiring decisions 
            powered by advanced AI.
          </p>
          <div className="d-flex gap-3">
            <Link to="/upload" className="btn btn-primary btn-lg">
              <i className="bi bi-upload me-2"></i>
              Get Started
            </Link>
            <Link to="/analytics" className="btn btn-outline-secondary btn-lg">
              <i className="bi bi-graph-up me-2"></i>
              View Analytics
            </Link>
          </div>
        </div>
        <div className="col-lg-6">
          <img 
            src="https://interviewdesk.ai/wp-content/uploads/2023/09/Unlocking-the-Power-of-Resume-Screening-AI_-A-Guide-for-HR-Professionals.png" 
            alt="AI Resume Screening" 
            className="img-fluid rounded shadow"
          />
        </div>
      </div>

      {/* Features Section */}
      <div className="row g-4 py-5">
        <div className="col-md-4">
          <div className="card h-100 border-0 shadow-sm card-hover">
            <div className="card-body text-center p-4">
              <div className="text-primary mb-3">
                <i className="bi bi-robot" style={{ fontSize: '3rem' }}></i>
              </div>
              <h4 className="card-title mb-3">AI Agents</h4>
              <p className="card-text text-muted">
                5 specialized AI agents work together: Resume Parser, Job Analyzer, 
                Skill Matcher, Scorer, and Feedback Generator.
              </p>
              <Link to="/agents" className="btn btn-outline-primary btn-sm mt-2">
                Learn More
              </Link>
            </div>
          </div>
        </div>

        <div className="col-md-4">
          <div className="card h-100 border-0 shadow-sm card-hover">
            <div className="card-body text-center p-4">
              <div className="text-success mb-3">
                <i className="bi bi-lightning-charge" style={{ fontSize: '3rem' }}></i>
              </div>
              <h4 className="card-title mb-3">Fast Processing</h4>
              <p className="card-text text-muted">
                Screen candidates in 3-5 seconds. Batch process up to 100 resumes 
                simultaneously with our optimized pipeline.
              </p>
              <Link to="/batch" className="btn btn-outline-success btn-sm mt-2">
                Try Batch
              </Link>
            </div>
          </div>
        </div>

        <div className="col-md-4">
          <div className="card h-100 border-0 shadow-sm card-hover">
            <div className="card-body text-center p-4">
              <div className="text-info mb-3">
                <i className="bi bi-graph-up-arrow" style={{ fontSize: '3rem' }}></i>
              </div>
              <h4 className="card-title mb-3">Analytics</h4>
              <p className="card-text text-muted">
                Track screening metrics, skill gaps, costs, and performance. 
                Export results for further analysis.
              </p>
              <Link to="/analytics" className="btn btn-outline-info btn-sm mt-2">
                View Dashboard
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="row py-5">
        <div className="col-12">
          <h2 className="text-center mb-5">How It Works</h2>
        </div>
        <div className="col-lg-10 mx-auto">
          <div className="timeline">
            <div className="timeline-item">
              <div className="card border-0 shadow-sm">
                <div className="card-body">
                  <h5 className="card-title">
                    <span className="badge bg-primary me-2">1</span>
                    Upload Files
                  </h5>
                  <p className="card-text text-muted">
                    Upload job descriptions and resumes (PDF or text). 
                    Files are securely stored and parsed.
                  </p>
                </div>
              </div>
            </div>

            <div className="timeline-item">
              <div className="card border-0 shadow-sm">
                <div className="card-body">
                  <h5 className="card-title">
                    <span className="badge bg-primary me-2">2</span>
                    AI Processing
                  </h5>
                  <p className="card-text text-muted">
                    AI agents extract structured data, analyze requirements, 
                    and match candidates to job requirements.
                  </p>
                </div>
              </div>
            </div>

            <div className="timeline-item">
              <div className="card border-0 shadow-sm">
                <div className="card-body">
                  <h5 className="card-title">
                    <span className="badge bg-primary me-2">3</span>
                    Scoring & Decision
                  </h5>
                  <p className="card-text text-muted">
                    Candidates are scored and categorized as HIRE, MAYBE, or REJECT 
                    based on configurable thresholds.
                  </p>
                </div>
              </div>
            </div>

            <div className="timeline-item">
              <div className="card border-0 shadow-sm">
                <div className="card-body">
                  <h5 className="card-title">
                    <span className="badge bg-primary me-2">4</span>
                    Feedback & Results
                  </h5>
                  <p className="card-text text-muted">
                    Receive personalized feedback, detailed match analysis, 
                    and exportable reports.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="row g-4 py-5 bg-light rounded p-4">
        <div className="col-md-3 text-center">
          <div className="display-4 fw-bold text-primary">5</div>
          <p className="text-muted mb-0">AI Agents</p>
        </div>
        <div className="col-md-3 text-center">
          <div className="display-4 fw-bold text-success">3-5s</div>
          <p className="text-muted mb-0">Processing Time</p>
        </div>
        <div className="col-md-3 text-center">
          <div className="display-4 fw-bold text-info">100+</div>
          <p className="text-muted mb-0">Batch Capacity</p>
        </div>
        <div className="col-md-3 text-center">
          <div className="display-4 fw-bold text-warning">$0.007</div>
          <p className="text-muted mb-0">Cost per Screen</p>
        </div>
      </div>

      {/* CTA Section */}
      <div className="row py-5">
        <div className="col-12 text-center">
          <h2 className="mb-4">Ready to streamline your hiring?</h2>
          <Link to="/upload" className="btn btn-primary btn-lg px-5">
            Start Screening Now
          </Link>
        </div>
      </div>
    </div>
  );
}

export default HomePage;
