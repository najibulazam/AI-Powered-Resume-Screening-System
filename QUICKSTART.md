# 🚀 Quick Reference Guide

## Starting the Application

### Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- URL: http://localhost:8000
- Docs: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm run dev
```
- URL: http://localhost:3000

## Common Commands

### Backend Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Create virtual environment
python -m venv venv

# Activate venv (Windows)
venv\Scripts\activate

# Activate venv (Linux/Mac)
source venv/bin/activate

# Run tests (if implemented)
pytest

# Check code style
flake8 app/

# Format code
black app/
```

### Frontend Commands
```bash
# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Environment Variables

### Backend (.env)
```env
GROQ_API_KEY=your_api_key_here
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## File Structure
```
Project Root/
├── backend/          # FastAPI backend
├── frontend/         # React frontend
├── README.md         # Full documentation
├── LICENSE           # MIT license
└── .gitignore        # Git ignore rules
```

## Useful URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |

## Troubleshooting

### Port already in use
```bash
# Backend (port 8000)
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Frontend (port 3000)
# Change port in vite.config.js or:
npm run dev -- --port 3001
```

### Module not found
```bash
# Backend
pip install -r requirements.txt

# Frontend
npm install
```

### API connection error
1. Ensure backend is running on port 8000
2. Check CORS settings in backend config
3. Verify frontend API URL in src/services/api.js

## Development Workflow

1. **Start Backend** → Terminal 1
2. **Start Frontend** → Terminal 2
3. **Upload Files** → Get file IDs
4. **Screen Candidates** → View results
5. **Check Logs** → Debug if needed

## API Quick Test

```bash
# Health check
curl http://localhost:8000/

# Upload job description
curl -X POST http://localhost:8000/api/upload/job-description \
  -F "file=@job.pdf"

# Screen candidate
curl -X POST http://localhost:8000/api/screen/process \
  -H "Content-Type: application/json" \
  -d '{
    "resume_file_id": "abc-123",
    "job_file_id": "def-456"
  }'
```

## Project Statistics

- **Backend**: ~3,000 lines of Python
- **Frontend**: ~2,000 lines of JavaScript/JSX
- **AI Agents**: 5 specialized agents
- **API Endpoints**: 20+ endpoints
- **Pages**: 6 main pages

## Support

- Read [README.md](README.md) for complete documentation
- Check API docs at http://localhost:8000/docs
- Open GitHub issues for bugs/features
