# 🤖 AI-Powered Resume Screening System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18.0+-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)

A production-ready full-stack AI system that automates resume screening using specialized AI agents. Built with FastAPI, React, and powered by Groq's LLaMA models for lightning-fast inference.

<div align="center">
  <img src="https://via.placeholder.com/800x400/0d6efd/ffffff?text=Agent-Based+Resume+Screening+System" alt="System Architecture" />
</div>

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [How It Works](#-how-it-works)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

## 🎯 Overview

This system revolutionizes the hiring process by leveraging AI agents to automatically screen resumes against job descriptions. Each agent specializes in a specific task, creating an intelligent pipeline that processes candidates efficiently and consistently.

### Why This Matters

- **Time Savings**: Screen 100+ candidates in minutes instead of hours
- **Consistency**: Eliminate human bias and screening fatigue
- **Scalability**: Process any volume of applications simultaneously
- **Cost-Effective**: Reduce screening costs by 90% using efficient LLM APIs
- **Transparency**: Get detailed feedback and reasoning for every decision

### Use Cases

- 🏢 **Enterprise Recruitment**: Handle hundreds of applications per job posting
- 👔 **Staffing Agencies**: Quick candidate evaluation across multiple clients
- 🚀 **Startups**: Automated screening without dedicated HR resources
- 📊 **HR Analytics**: Data-driven insights into candidate pools

## ✨ Key Features

### 🎯 AI Agent Pipeline

Five specialized AI agents work together to screen candidates:

1. **Resume Parser Agent** 
   - Extracts structured data from unstructured resumes
   - Handles PDF and text files
   - Validates and normalizes information

2. **Job Analyzer Agent**
   - Analyzes job descriptions
   - Identifies required vs. preferred skills
   - Determines experience requirements

3. **Skill Matcher Agent**
   - Compares candidate skills to job requirements
   - Categorizes skills (required, preferred, missing)
   - Calculates match percentages

4. **Scorer Agent**
   - Makes hiring decisions: HIRE, MAYBE, or REJECT
   - Provides confidence levels (high, medium, low)
   - Flags candidates needing human review

5. **Feedback Generator Agent**
   - Creates personalized feedback for candidates
   - Explains decisions transparently
   - Suggests improvement areas

### 🚀 Core Capabilities

- **Single Candidate Screening**: Deep analysis with detailed feedback
- **Batch Processing**: Screen up to 100 candidates simultaneously
- **Real-time Progress Tracking**: Monitor screening status in real-time
- **Analytics Dashboard**: Visualize screening metrics and costs
- **Data Export**: Download results as CSV or JSON
- **RESTful API**: Integrate with existing HR systems
- **Responsive UI**: Works seamlessly on desktop and mobile

### 🔒 Production Features

- **Rate Limiting**: Prevent API abuse (configurable per endpoint)
- **CORS Support**: Secure cross-origin requests
- **Error Handling**: Graceful failure recovery
- **Logging**: Comprehensive logging for debugging
- **File Validation**: Secure file upload with type/size checks
- **Cost Tracking**: Monitor LLM API usage costs

## 🏗️ Architecture

### System Design

The system follows a multi-agent architecture where each agent has a single responsibility:

```
┌──────────────┐
│   Frontend   │  React SPA (User Interface)
└──────┬───────┘
       │ HTTP/REST
┌──────▼───────────────────────────────────┐
│         FastAPI Backend                  │
│  ┌────────────────────────────────────┐  │
│  │    Orchestration Service           │  │ Coordinates agent pipeline
│  └─────────┬──────────────────────────┘  │
│            │                             │
│  ┌─────────▼────────┐   ┌──────────────┐ │
│  │  Resume Parser   │   │ Job Analyzer │ │ Phase 1: Extract data
│  └─────────┬────────┘   └──────┬───────┘ │
│            │                   │         │
│  ┌─────────▼───────────────────▼───────┐ │
│  │       Skill Matcher Agent           │ │ Phase 2: Compare
│  └─────────┬───────────────────────────┘ │
│            │                             │
│  ┌─────────▼───────────┐   ┌───────────┐ │
│  │    Scorer Agent     │   │ Feedback  │ │ Phase 3: Decide
│  └─────────────────────┘   │ Generator │ │
│                            └───────────┘ │
└──────────────────────────────────────────┘
       │
       ▼
┌──────────────┐
│  Groq API    │  LLaMA 70B (LLM Inference)
└──────────────┘
```

### Agent Communication Flow

```
User → Upload Files → Store with UUID
  ↓
User → Request Screening (with UUIDs)
  ↓
Orchestrator → Resume Parser Agent → Parse resume text
  ↓
Orchestrator → Job Analyzer Agent → Parse job requirements
  ↓
Orchestrator → Skill Matcher Agent → Compare & match
  ↓
Orchestrator → Scorer Agent → Make decision
  ↓
Orchestrator → Feedback Generator → Create feedback
  ↓
User ← Complete Result ← Orchestrator
```

## 🎬 How It Works

### 1. Upload Phase

```
User uploads:
├─ Job Description (PDF/TXT) → Saved with unique file_id
└─ Resumes (PDF/TXT, multiple) → Each saved with unique file_id
```

### 2. Screening Phase

For each candidate:

**Step 1: Extract Information**
- Resume Parser Agent extracts name, skills, experience, education
- Job Analyzer Agent extracts required skills, experience, qualifications

**Step 2: Match & Score**
- Skill Matcher identifies matched and missing skills
- Scorer calculates overall fit score (0-100)
- Decision engine applies thresholds:
  - ≥75: HIRE (strong match)
  - 50-74: MAYBE (moderate match, review needed)
  - <50: REJECT (weak match)

**Step 3: Generate Feedback**
- Feedback Generator creates personalized message
- Highlights strengths and areas for improvement
- Provides actionable suggestions

### 3. Results Phase

```
Output:
├─ Decision: HIRE | MAYBE | REJECT
├─ Overall Score: 0-100
├─ Confidence: HIGH | MEDIUM | LOW
├─ Matched Skills: [list]
├─ Missing Skills: [list]
├─ Strengths: [list]
├─ Weaknesses: [list]
├─ Feedback Message: Personalized text
└─ Metadata: processing time, cost, review flags
```

### Example Workflow

```bash
# 1. Upload job description
POST /api/upload/job-description
Response: { file_id: "abc-123" }

# 2. Upload resumes
POST /api/upload/resumes
Response: { file_ids: ["def-456", "ghi-789"] }

# 3. Screen candidate
POST /api/screen/process
{
  "resume_file_id": "def-456",
  "job_file_id": "abc-123",
  "include_feedback": true,
  "custom_thresholds": {
    "hire": 75,
    "reject": 50
  }
}

# 4. Get result
Response: {
  "success": true,
  "result": {
    "decision": "HIRE",
    "overall_score": 85.5,
    "confidence": "high",
    "matched_skills": ["Python", "FastAPI", "React"],
    "missing_skills": ["Kubernetes"],
    "feedback_message": "Strong technical background..."
  }
}
```

## 🛠️ Tech Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast Python web framework
- **Language**: Python 3.9+
- **LLM Provider**: [Groq](https://groq.com/) - Ultra-fast LLM inference
- **Model**: LLaMA 3.1 70B - High-performance open-source LLM
- **PDF Processing**: PyPDF2 - PDF text extraction
- **Validation**: Pydantic - Data validation and serialization
- **Server**: Uvicorn - ASGI server

### Frontend
- **Framework**: [React 18](https://react.dev/) - UI library
- **Build Tool**: [Vite](https://vitejs.dev/) - Next-gen frontend tooling
- **Styling**: [Bootstrap 5](https://getbootstrap.com/) - CSS framework
- **Icons**: Bootstrap Icons
- **HTTP Client**: Axios - Promise-based HTTP client
- **Routing**: React Router v6 - Client-side routing

### Infrastructure
- **API Design**: RESTful architecture
- **File Storage**: Local filesystem (production: S3/Azure Blob)
- **Rate Limiting**: SlowAPI
- **CORS**: FastAPI middleware
- **Logging**: Python logging module

## 📦 Installation

### Prerequisites

- **Python 3.9+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** ([Download](https://nodejs.org/))
- **Groq API Key** ([Get free key](https://console.groq.com/))

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/resume-screening-system.git
cd resume-screening-system
```

### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "GROQ_API_KEY=your_groq_api_key_here" > .env
```

### Step 3: Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install
```

## ⚙️ Configuration

### Backend Configuration (.env)

Create a `.env` file in the `backend` directory:

```env
# Required
GROQ_API_KEY=gsk_your_api_key_here

# Optional (defaults shown)
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# LLM Configuration
LLM_MODEL=llama-3.1-70b-versatile
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2000

# File Upload Limits
MAX_UPLOAD_SIZE_MB=10
ALLOWED_EXTENSIONS=.pdf,.txt

# Rate Limiting
RATE_LIMIT_PER_MINUTE=30

# API Key (optional, for authentication)
API_KEY=
```

### Frontend Configuration

The frontend automatically connects to `http://localhost:8000`. To change:

Edit `frontend/src/services/api.js`:

```javascript
const API_BASE_URL = 'http://your-backend-url:8000';
```

## 🚀 Usage

### Starting the Application

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access the Application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

### Quick Start Guide

#### 1. Upload Files

Navigate to the **Upload** page:

1. **Upload Job Description**
   - Click "Choose File" under Job Description
   - Select a PDF or TXT file
   - Click "Upload Job Description"
   - Copy the returned `file_id`

2. **Upload Resumes**
   - Click "Choose Files" under Resumes (multiple allowed)
   - Select PDF or TXT files
   - Click "Upload Resumes"
   - Copy the returned `file_ids`

#### 2. Screen Single Candidate

Navigate to the **Screening** page:

1. Paste the resume `file_id`
2. Paste the job description `file_id`
3. (Optional) Adjust thresholds:
   - Hire Threshold: Default 75
   - Reject Threshold: Default 50
4. (Optional) Toggle feedback options
5. Click "Start Screening"
6. View detailed results including:
   - Decision (HIRE/MAYBE/REJECT)
   - Overall score
   - Matched and missing skills
   - Strengths and weaknesses
   - Personalized feedback

#### 3. Batch Processing

Navigate to the **Batch Processing** page:

1. Paste the job description `file_id`
2. Paste multiple resume `file_ids` (one per line)
3. Configure screening options
4. Click "Start Batch Processing"
5. Monitor real-time progress
6. View aggregated results:
   - HIRE/MAYBE/REJECT counts
   - Individual candidate details
   - Total cost and processing time

#### 4. View Analytics

Navigate to the **Analytics** page:

- **Dashboard**: Overall statistics and charts
- **Cost Analysis**: Calculate costs for different volumes
- **Export Data**: Download results as CSV or JSON

#### 5. Test AI Agents

Navigate to the **AI Agents** page:

- Test individual agents with sample data
- See agent inputs and outputs
- Understand the screening pipeline

## 📚 API Documentation

### Interactive Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Upload Endpoints

```http
POST /api/upload/job-description
POST /api/upload/resumes
```

#### Screening Endpoints

```http
POST /api/screen/process           # Single candidate
POST /api/screen/batch             # Multiple candidates
GET  /api/screen/batch/{batch_id}  # Batch status
```

#### Analytics Endpoints

```http
GET  /api/analytics/dashboard      # Dashboard stats
POST /api/analytics/skill-gap      # Skill gap analysis
POST /api/analytics/cost          # Cost calculation
POST /api/analytics/export        # Export data
```

#### Individual Agent Endpoints

```http
POST /api/agents/parse-resume      # Resume Parser
POST /api/agents/analyze-job       # Job Analyzer
POST /api/agents/match-skills      # Skill Matcher
POST /api/agents/score             # Scorer
POST /api/agents/generate-feedback # Feedback Generator
```

### Example API Calls

**Upload Job Description:**
```bash
curl -X POST "http://localhost:8000/api/upload/job-description" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@job_description.pdf"
```

**Screen Candidate:**
```bash
curl -X POST "http://localhost:8000/api/screen/process" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_file_id": "abc-123",
    "job_file_id": "def-456",
    "include_feedback": true,
    "custom_thresholds": {
      "hire": 75,
      "reject": 50
    }
  }'
```

## 📁 Project Structure

```
resume-screening-system/
│
├── backend/                      # FastAPI Backend
│   ├── app/
│   │   ├── agents/              # AI Agents
│   │   │   ├── __init__.py
│   │   │   ├── resume_parser.py
│   │   │   ├── job_analyzer.py
│   │   │   ├── skill_matcher.py
│   │   │   ├── scorer.py
│   │   │   └── feedback_generator.py
│   │   │
│   │   ├── schemas/             # Pydantic Models
│   │   │   ├── __init__.py
│   │   │   ├── resume.py
│   │   │   ├── job_description.py
│   │   │   ├── matching.py
│   │   │   ├── scoring.py
│   │   │   ├── feedback.py
│   │   │   ├── orchestration.py
│   │   │   ├── analytics.py
│   │   │   └── upload.py
│   │   │
│   │   ├── services/            # Business Logic
│   │   │   ├── orchestrator.py  # Pipeline coordination
│   │   │   ├── analytics.py     # Analytics service
│   │   │   └── database.py      # Database operations
│   │   │
│   │   ├── utils/               # Utilities
│   │   │   ├── __init__.py
│   │   │   ├── file_handler.py  # File operations
│   │   │   └── pdf_parser.py    # PDF extraction
│   │   │
│   │   ├── models/              # Database Models
│   │   │   ├── __init__.py
│   │   │   └── database.py
│   │   │
│   │   ├── __init__.py
│   │   ├── config.py            # Configuration
│   │   └── main.py              # FastAPI app
│   │
│   ├── uploads/                 # Uploaded Files
│   │   ├── job_descriptions/
│   │   └── resumes/
│   │
│   ├── requirements.txt         # Python dependencies
│   ├── init.sql                 # Database schema
│   └── run_server.ps1           # Startup script
│
├── frontend/                    # React Frontend
│   ├── src/
│   │   ├── components/          # Reusable Components
│   │   │   ├── Navbar.jsx
│   │   │   ├── LoadingSpinner.jsx
│   │   │   ├── ErrorAlert.jsx
│   │   │   └── DecisionBadge.jsx
│   │   │
│   │   ├── pages/               # Page Components
│   │   │   ├── HomePage.jsx
│   │   │   ├── UploadPage.jsx
│   │   │   ├── ScreeningPage.jsx
│   │   │   ├── BatchScreeningPage.jsx
│   │   │   ├── AnalyticsPage.jsx
│   │   │   └── AgentsPage.jsx
│   │   │
│   │   ├── services/            # API Client
│   │   │   └── api.js
│   │   │
│   │   ├── utils/               # Utilities
│   │   │   └── helpers.js
│   │   │
│   │   ├── App.jsx              # Root component
│   │   ├── main.jsx             # Entry point
│   │   └── index.css            # Global styles
│   │
│   ├── public/                  # Static assets
│   ├── index.html               # HTML template
│   ├── package.json             # Dependencies
│   ├── vite.config.js           # Vite configuration
│   └── start.ps1                # Startup script
│
└── README.md                    # This file
```

## 🎯 Performance & Costs

### Processing Speed

- **Single Candidate**: 2-5 seconds average
- **Batch (10 candidates)**: 20-50 seconds
- **Batch (100 candidates)**: 3-8 minutes

### Cost Analysis (Groq API)

| Volume | Cost per Candidate | Total Cost |
|--------|-------------------|------------|
| 1 candidate | $0.005 - $0.01 | $0.005 - $0.01 |
| 10 candidates | $0.005 | $0.05 - $0.10 |
| 100 candidates | $0.004 | $0.40 - $0.80 |
| 1000 candidates | $0.003 | $3.00 - $6.00 |

*Note: Groq offers free tier with generous limits. Costs decrease with volume.*

### Scalability

- Horizontal scaling: Add more API workers
- Async processing: Queue-based batch processing (future enhancement)
- Caching: Cache parsed job descriptions for multiple candidates
- Database: Add PostgreSQL for production (currently file-based)

## 🚧 Roadmap

### Phase 1 (Current) ✅
- [x] Core agent pipeline
- [x] Single & batch screening
- [x] React frontend
- [x] Analytics dashboard

### Phase 2 (Planned)
- [ ] PostgreSQL database integration
- [ ] User authentication & authorization
- [ ] Team collaboration features
- [ ] Email notifications
- [ ] Resume builder recommendations
- [ ] Interview question generator

### Phase 3 (Future)
- [ ] Redis caching layer
- [ ] Celery task queue for async processing
- [ ] WebSocket real-time updates
- [ ] Advanced analytics with ML insights
- [ ] Integration with ATS systems (Greenhouse, Lever)
- [ ] Custom agent training/fine-tuning

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use ESLint/Prettier for JavaScript code
- Write docstrings for all functions
- Add unit tests for new features
- Update documentation as needed

## 🐛 Troubleshooting

### Common Issues

**Backend won't start:**
```bash
# Check Python version
python --version  # Should be 3.9+

# Verify dependencies
pip install -r requirements.txt

# Check .env file exists
ls .env
```

**Frontend won't start:**
```bash
# Check Node version
node --version  # Should be 18+

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**API connection errors:**
- Verify backend is running on port 8000
- Check CORS settings in backend config
- Ensure frontend API URL is correct

**LLM errors:**
- Verify Groq API key is valid
- Check API rate limits
- Monitor Groq API status

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Groq](https://groq.com/) - Lightning-fast LLM inference
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - Frontend library
- [Bootstrap](https://getbootstrap.com/) - CSS framework
- [Meta LLaMA](https://ai.meta.com/llama/) - Open-source LLM

## 📞 Support

For questions, issues, or suggestions:

- **Issues**: [GitHub Issues](https://github.com/yourusername/resume-screening-system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/resume-screening-system/discussions)
- **Email**: support@example.com

---

<div align="center">

**Built with ❤️ using AI Agents**

⭐ Star this repo if you find it helpful!

[Report Bug](https://github.com/yourusername/resume-screening-system/issues) · 
[Request Feature](https://github.com/yourusername/resume-screening-system/issues) · 
[Documentation](https://github.com/yourusername/resume-screening-system/wiki)

</div>
