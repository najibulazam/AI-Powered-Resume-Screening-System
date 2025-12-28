# Contributing to AI-Powered Resume Screening System

First off, thank you for considering contributing to this project! 🎉

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code:

- Be respectful and inclusive
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards others

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Screenshots** (if applicable)
- **Environment details** (OS, Python version, Node version)

Example:
```markdown
**Bug**: Resume parser fails with non-ASCII characters

**Steps to Reproduce**:
1. Upload resume with Chinese characters
2. Call parse-resume endpoint
3. See error

**Expected**: Parse successfully
**Actual**: 500 error

**Environment**: Windows 11, Python 3.11, Backend v1.0
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. Include:

- **Clear use case** - Why is this needed?
- **Proposed solution** - How should it work?
- **Alternatives considered** - What else did you think about?

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Test thoroughly**
5. **Commit with clear messages**
6. **Push to your fork**
7. **Open a Pull Request**

## Development Setup

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Dev dependencies (if exists)
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Running Tests

```bash
# Backend
pytest

# Frontend
npm test
```

## Coding Standards

### Python (Backend)

- Follow **PEP 8** style guide
- Use **type hints** for function signatures
- Write **docstrings** for all public functions
- Keep functions **small and focused**
- Use **meaningful variable names**

Example:
```python
def calculate_match_score(
    required_skills: List[str],
    candidate_skills: List[str]
) -> float:
    """
    Calculate skill match percentage.
    
    Args:
        required_skills: Skills required for the job
        candidate_skills: Skills the candidate has
    
    Returns:
        Match percentage (0-100)
    
    Example:
        >>> calculate_match_score(["Python", "React"], ["Python"])
        50.0
    """
    if not required_skills:
        return 0.0
    
    matched = set(required_skills) & set(candidate_skills)
    return (len(matched) / len(required_skills)) * 100
```

### JavaScript/React (Frontend)

- Use **ES6+ features**
- Follow **Airbnb style guide**
- Use **functional components** with hooks
- Keep components **small and reusable**
- Use **prop-types** or TypeScript

Example:
```javascript
/**
 * Display a candidate's screening decision
 * @param {Object} props
 * @param {string} props.decision - HIRE, MAYBE, or REJECT
 * @param {number} props.score - Overall score (0-100)
 */
function DecisionBadge({ decision, score }) {
  const badgeClass = getBadgeClass(decision);
  
  return (
    <div className={`badge ${badgeClass}`}>
      {decision} ({score.toFixed(1)})
    </div>
  );
}
```

### File Organization

- **Keep related code together**
- **One component per file** (frontend)
- **One agent per file** (backend)
- **Descriptive file names**

### Comments

- Write comments for **complex logic**
- Explain **why, not what**
- Keep comments **up to date**

Good:
```python
# Use exponential backoff to handle rate limits gracefully
await asyncio.sleep(2 ** retry_count)
```

Bad:
```python
# Sleep for 2 seconds
await asyncio.sleep(2)
```

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(agent): add support for .docx resumes

- Add python-docx dependency
- Implement DOCX parser in file_handler
- Update upload validation

Closes #123
```

```
fix(frontend): handle null values in screening results

Previously caused TypeError when confidence was undefined.
Now displays 'N/A' for missing values.

Fixes #456
```

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No console errors/warnings

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Screenshots (if applicable)
Add screenshots

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
```

### Review Process

1. **Automated checks** must pass (linting, tests)
2. **At least one approval** required
3. **Address review comments**
4. **Squash commits** if needed
5. **Merge** when approved

## Areas to Contribute

### High Priority
- [ ] PostgreSQL database integration
- [ ] User authentication
- [ ] Email notifications
- [ ] Unit tests
- [ ] Integration tests

### Medium Priority
- [ ] Resume format support (.docx, .odt)
- [ ] Advanced analytics
- [ ] Batch progress WebSocket
- [ ] Export to PDF reports

### Low Priority
- [ ] Dark mode
- [ ] Internationalization (i18n)
- [ ] Mobile app
- [ ] Browser extension

## Questions?

- Open a [Discussion](https://github.com/najibulazam/AI-Powered-Resume-Screening-System/discussions)
- Email: azam.mdnajibul@gmail.com

## Recognition

Contributors will be added to our [README.md](README.md) file!

Thank you for making this project better! 🚀
