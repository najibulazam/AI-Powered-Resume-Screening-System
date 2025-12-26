import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import UploadPage from './pages/UploadPage';
import ScreeningPage from './pages/ScreeningPage';
import BatchScreeningPage from './pages/BatchScreeningPage';
import AnalyticsPage from './pages/AnalyticsPage';
import AgentsPage from './pages/AgentsPage';

function App() {
  return (
    <Router>
      <div className="app">
        <Navbar />
        <div className="container-fluid py-4">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/screening" element={<ScreeningPage />} />
            <Route path="/batch" element={<BatchScreeningPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/agents" element={<AgentsPage />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
