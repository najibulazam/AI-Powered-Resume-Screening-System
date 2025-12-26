import React from 'react';

function ErrorAlert({ error, onDismiss }) {
  if (!error) return null;

  return (
    <div className="alert alert-danger alert-dismissible fade show" role="alert">
      <i className="bi bi-exclamation-triangle me-2"></i>
      {error}
      {onDismiss && (
        <button 
          type="button" 
          className="btn-close" 
          onClick={onDismiss}
        ></button>
      )}
    </div>
  );
}

export default ErrorAlert;
