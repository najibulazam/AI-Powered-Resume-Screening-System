import React from 'react';

function LoadingSpinner({ message = 'Loading...', size = 'large' }) {
  const spinnerSize = size === 'small' ? 'spinner-border-sm' : '';
  const textSize = size === 'small' ? 'small' : '';

  return (
    <div className="text-center py-5">
      <div className={`spinner-border text-primary ${spinnerSize}`} role="status">
        <span className="visually-hidden">{message}</span>
      </div>
      {message && <p className={`mt-3 text-muted ${textSize}`}>{message}</p>}
    </div>
  );
}

export default LoadingSpinner;
