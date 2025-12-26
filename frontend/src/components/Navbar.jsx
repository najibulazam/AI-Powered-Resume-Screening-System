import React from 'react';
import { Link, useLocation } from 'react-router-dom';

function Navbar() {
  const location = useLocation();
  
  const isActive = (path) => {
    return location.pathname === path ? 'active' : '';
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm">
      <div className="container-fluid">
        <Link className="navbar-brand fw-bold" to="/">
          <i className="bi bi-robot me-2"></i>
          Resume Screening AI
        </Link>
        <button 
          className="navbar-toggler" 
          type="button" 
          data-bs-toggle="collapse" 
          data-bs-target="#navbarNav"
        >
          <span className="navbar-toggler-icon"></span>
        </button>
        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav ms-auto">
            <li className="nav-item">
              <Link className={`nav-link ${isActive('/')}`} to="/">
                <i className="bi bi-house-door me-1"></i>
                Home
              </Link>
            </li>
            <li className="nav-item">
              <Link className={`nav-link ${isActive('/upload')}`} to="/upload">
                <i className="bi bi-cloud-upload me-1"></i>
                Upload
              </Link>
            </li>
            <li className="nav-item">
              <Link className={`nav-link ${isActive('/screening')}`} to="/screening">
                <i className="bi bi-search me-1"></i>
                Screening
              </Link>
            </li>
            <li className="nav-item">
              <Link className={`nav-link ${isActive('/batch')}`} to="/batch">
                <i className="bi bi-collection me-1"></i>
                Batch Processing
              </Link>
            </li>
            <li className="nav-item">
              <Link className={`nav-link ${isActive('/analytics')}`} to="/analytics">
                <i className="bi bi-graph-up me-1"></i>
                Analytics
              </Link>
            </li>
            <li className="nav-item">
              <Link className={`nav-link ${isActive('/agents')}`} to="/agents">
                <i className="bi bi-cpu me-1"></i>
                AI Agents
              </Link>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
