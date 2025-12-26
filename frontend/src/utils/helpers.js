export const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

export const getDecisionColor = (decision) => {
  switch (decision?.toUpperCase()) {
    case 'HIRE': return 'success';
    case 'MAYBE': return 'warning';
    case 'REJECT': return 'danger';
    default: return 'secondary';
  }
};

export const getScoreColor = (score) => {
  if (score >= 75) return 'success';
  if (score >= 50) return 'warning';
  return 'danger';
};

export const truncateText = (text, maxLength = 100) => {
  if (!text || text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

export const parseFileIds = (input) => {
  // Parse comma or newline separated file IDs
  return input
    .split(/[,\n]/)
    .map(id => id.trim())
    .filter(id => id.length > 0);
};

export const calculatePercentage = (value, total) => {
  if (!total || total === 0) return 0;
  return ((value / total) * 100).toFixed(1);
};

export const formatCurrency = (amount, decimals = 2) => {
  if (!amount && amount !== 0) return '$0.00';
  return `$${parseFloat(amount).toFixed(decimals)}`;
};

export const formatDuration = (milliseconds) => {
  if (!milliseconds) return '0ms';
  if (milliseconds < 1000) return `${milliseconds.toFixed(0)}ms`;
  const seconds = milliseconds / 1000;
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const minutes = seconds / 60;
  return `${minutes.toFixed(1)}m`;
};
