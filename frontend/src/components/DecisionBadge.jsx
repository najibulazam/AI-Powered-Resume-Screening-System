import React from 'react';

function DecisionBadge({ decision, size = 'md' }) {
  if (!decision) return null;

  const getBadgeClass = () => {
    switch (decision.toUpperCase()) {
      case 'HIRE': return 'badge-hire';
      case 'MAYBE': return 'badge-maybe';
      case 'REJECT': return 'badge-reject';
      default: return 'bg-secondary';
    }
  };

  const sizeClass = size === 'lg' ? 'fs-3' : size === 'sm' ? 'fs-6' : '';

  return (
    <span className={`badge ${getBadgeClass()} ${sizeClass}`}>
      {decision.toUpperCase()}
    </span>
  );
}

export default DecisionBadge;
