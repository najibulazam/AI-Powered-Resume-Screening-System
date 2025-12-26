import React, { useState, useEffect } from 'react';
import { getDashboardAnalytics, exportResults } from '../services/api';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Bar, Pie } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

function AnalyticsPage() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState('all_time');
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await getDashboardAnalytics(timeRange);
      if (response.data.success) {
        setAnalytics(response.data);
      } else {
        setError(response.data.error || 'Failed to load analytics');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    setExporting(true);

    try {
      const response = await exportResults({
        format: format,
        include_feedback: true,
        include_skills: true
      });

      if (response.data.success) {
        // Create download link
        const blob = new Blob([response.data.data], {
          type: format === 'csv' ? 'text/csv' : 'application/json'
        });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = response.data.file_name;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (err) {
      setError('Failed to export results');
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="container">
        <div className="text-center py-5">
          <div className="spinner-border text-primary" style={{ width: '3rem', height: '3rem' }}>
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-3 text-muted">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <div className="alert alert-danger">
          <i className="bi bi-exclamation-triangle me-2"></i>
          {error}
        </div>
      </div>
    );
  }

  if (!analytics) {
    return null;
  }

  const decisionStats = analytics.decision_stats || {};
  const costAnalysis = analytics.cost_analysis || {};
  const performanceMetrics = analytics.performance_metrics || {};

  // Chart data for decisions
  const decisionChartData = {
    labels: ['HIRE', 'MAYBE', 'REJECT'],
    datasets: [
      {
        label: 'Candidates',
        data: [
          decisionStats.hire_count || 0,
          decisionStats.maybe_count || 0,
          decisionStats.reject_count || 0,
        ],
        backgroundColor: [
          'rgba(25, 135, 84, 0.8)',
          'rgba(255, 193, 7, 0.8)',
          'rgba(220, 53, 69, 0.8)',
        ],
        borderColor: [
          'rgba(25, 135, 84, 1)',
          'rgba(255, 193, 7, 1)',
          'rgba(220, 53, 69, 1)',
        ],
        borderWidth: 2,
      },
    ],
  };

  return (
    <div className="container">
      <div className="row mb-4">
        <div className="col-12">
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <h1 className="mb-2">
                <i className="bi bi-graph-up text-primary me-2"></i>
                Analytics Dashboard
              </h1>
              <p className="text-muted mb-0">
                Track screening performance, costs, and insights
              </p>
            </div>
            <div>
              <select
                className="form-select"
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
              >
                <option value="today">Today</option>
                <option value="this_week">This Week</option>
                <option value="this_month">This Month</option>
                <option value="all_time">All Time</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Overview Stats */}
      <div className="row g-4 mb-4">
        <div className="col-md-3">
          <div className="card stat-card stat-primary shadow-sm">
            <div className="card-body">
              <h6 className="text-muted mb-2">Total Screenings</h6>
              <h2 className="mb-0">{decisionStats.total_screenings || 0}</h2>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card stat-card stat-success shadow-sm">
            <div className="card-body">
              <h6 className="text-muted mb-2">Candidates to Hire</h6>
              <h2 className="mb-0">{decisionStats.hire_count || 0}</h2>
              <small className="text-muted">
                {decisionStats.hire_percent?.toFixed(1) || 0}%
              </small>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card stat-card stat-warning shadow-sm">
            <div className="card-body">
              <h6 className="text-muted mb-2">Maybe Candidates</h6>
              <h2 className="mb-0">{decisionStats.maybe_count || 0}</h2>
              <small className="text-muted">
                {decisionStats.maybe_percent?.toFixed(1) || 0}%
              </small>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card stat-card stat-danger shadow-sm">
            <div className="card-body">
              <h6 className="text-muted mb-2">Rejected</h6>
              <h2 className="mb-0">{decisionStats.reject_count || 0}</h2>
              <small className="text-muted">
                {decisionStats.reject_percent?.toFixed(1) || 0}%
              </small>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="row g-4 mb-4">
        <div className="col-lg-8">
          <div className="card shadow-sm">
            <div className="card-header">
              <h5 className="mb-0">
                <i className="bi bi-bar-chart me-2"></i>
                Decision Distribution
              </h5>
            </div>
            <div className="card-body">
              <Bar
                data={decisionChartData}
                options={{
                  responsive: true,
                  maintainAspectRatio: true,
                  plugins: {
                    legend: {
                      display: false,
                    },
                    title: {
                      display: false,
                    },
                  },
                  scales: {
                    y: {
                      beginAtZero: true,
                      ticks: {
                        precision: 0,
                      },
                    },
                  },
                }}
              />
            </div>
          </div>
        </div>

        <div className="col-lg-4">
          <div className="card shadow-sm">
            <div className="card-header">
              <h5 className="mb-0">
                <i className="bi bi-pie-chart me-2"></i>
                Decision Breakdown
              </h5>
            </div>
            <div className="card-body">
              <Pie
                data={decisionChartData}
                options={{
                  responsive: true,
                  maintainAspectRatio: true,
                  plugins: {
                    legend: {
                      position: 'bottom',
                    },
                  },
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Cost Analysis */}
      <div className="row g-4 mb-4">
        <div className="col-lg-6">
          <div className="card shadow-sm">
            <div className="card-header">
              <h5 className="mb-0">
                <i className="bi bi-currency-dollar me-2"></i>
                Cost Analysis
              </h5>
            </div>
            <div className="card-body">
              <div className="row g-3">
                <div className="col-6">
                  <div className="border-start border-primary border-4 ps-3">
                    <h6 className="text-muted mb-1">Total Spent</h6>
                    <h3 className="mb-0">${costAnalysis.total_cost?.toFixed(4) || '0.00'}</h3>
                  </div>
                </div>
                <div className="col-6">
                  <div className="border-start border-info border-4 ps-3">
                    <h6 className="text-muted mb-1">Avg per Candidate</h6>
                    <h3 className="mb-0">${costAnalysis.avg_cost_per_screening?.toFixed(4) || '0.00'}</h3>
                  </div>
                </div>
                <div className="col-6">
                  <div className="border-start border-success border-4 ps-3">
                    <h6 className="text-muted mb-1">Monthly Est.</h6>
                    <h3 className="mb-0">${costAnalysis.monthly_projection?.toFixed(2) || '0.00'}</h3>
                  </div>
                </div>
                <div className="col-6">
                  <div className="border-start border-warning border-4 ps-3">
                    <h6 className="text-muted mb-1">Annual Est.</h6>
                    <h3 className="mb-0">${costAnalysis.annual_projection?.toFixed(2) || '0.00'}</h3>
                  </div>
                </div>
              </div>

              {costAnalysis.phase_costs && (
                <div className="mt-4">
                  <h6 className="mb-3">Cost Breakdown by Phase</h6>
                  <div className="table-responsive">
                    <table className="table table-sm">
                      <tbody>
                        {Object.entries(costAnalysis.phase_costs).map(([phase, cost]) => (
                          <tr key={phase}>
                            <td className="text-capitalize">{phase.replace('_', ' ')}</td>
                            <td className="text-end fw-bold">${cost.toFixed(4)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="col-lg-6">
          <div className="card shadow-sm">
            <div className="card-header">
              <h5 className="mb-0">
                <i className="bi bi-speedometer2 me-2"></i>
                Performance Metrics
              </h5>
            </div>
            <div className="card-body">
              <div className="row g-3">
                <div className="col-6">
                  <div className="border-start border-primary border-4 ps-3">
                    <h6 className="text-muted mb-1">Avg Score</h6>
                    <h3 className="mb-0">{performanceMetrics.avg_score?.toFixed(1) || '0'}</h3>
                  </div>
                </div>
                <div className="col-6">
                  <div className="border-start border-info border-4 ps-3">
                    <h6 className="text-muted mb-1">Avg Confidence</h6>
                    <h3 className="mb-0">{performanceMetrics.avg_confidence?.toFixed(1) || '0'}%</h3>
                  </div>
                </div>
                <div className="col-6">
                  <div className="border-start border-success border-4 ps-3">
                    <h6 className="text-muted mb-1">Avg Time</h6>
                    <h3 className="mb-0">{performanceMetrics.avg_processing_time_ms?.toFixed(0) || '0'}ms</h3>
                  </div>
                </div>
                <div className="col-6">
                  <div className="border-start border-warning border-4 ps-3">
                    <h6 className="text-muted mb-1">Success Rate</h6>
                    <h3 className="mb-0">{performanceMetrics.success_rate?.toFixed(1) || '0'}%</h3>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Top Missing Skills */}
      {analytics.top_missing_skills && analytics.top_missing_skills.length > 0 && (
        <div className="row mb-4">
          <div className="col-12">
            <div className="card shadow-sm">
              <div className="card-header">
                <h5 className="mb-0">
                  <i className="bi bi-exclamation-triangle me-2"></i>
                  Most Common Skill Gaps
                </h5>
              </div>
              <div className="card-body">
                <div className="table-responsive">
                  <table className="table table-hover">
                    <thead>
                      <tr>
                        <th>Skill</th>
                        <th>Frequency</th>
                        <th>Importance</th>
                        <th>Avg Gap Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analytics.top_missing_skills.slice(0, 10).map((skill, index) => (
                        <tr key={index}>
                          <td className="fw-bold">{skill.skill_name}</td>
                          <td>
                            <span className="badge bg-primary">{skill.frequency}</span>
                          </td>
                          <td>
                            <span className={`badge ${
                              skill.importance === 'critical' ? 'bg-danger' :
                              skill.importance === 'important' ? 'bg-warning' :
                              'bg-secondary'
                            }`}>
                              {skill.importance}
                            </span>
                          </td>
                          <td>{skill.avg_gap_score?.toFixed(1)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Export Section */}
      <div className="row">
        <div className="col-12">
          <div className="card shadow-sm">
            <div className="card-header">
              <h5 className="mb-0">
                <i className="bi bi-download me-2"></i>
                Export Data
              </h5>
            </div>
            <div className="card-body">
              <p className="text-muted mb-3">
                Export screening results and analytics for further analysis
              </p>
              <div className="d-flex gap-2">
                <button
                  className="btn btn-primary"
                  onClick={() => handleExport('csv')}
                  disabled={exporting}
                >
                  {exporting ? (
                    <span className="spinner-border spinner-border-sm me-2"></span>
                  ) : (
                    <i className="bi bi-filetype-csv me-2"></i>
                  )}
                  Export as CSV
                </button>
                <button
                  className="btn btn-outline-primary"
                  onClick={() => handleExport('json')}
                  disabled={exporting}
                >
                  {exporting ? (
                    <span className="spinner-border spinner-border-sm me-2"></span>
                  ) : (
                    <i className="bi bi-filetype-json me-2"></i>
                  )}
                  Export as JSON
                </button>
                <button
                  className="btn btn-outline-secondary"
                  onClick={fetchAnalytics}
                >
                  <i className="bi bi-arrow-clockwise me-2"></i>
                  Refresh
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AnalyticsPage;
