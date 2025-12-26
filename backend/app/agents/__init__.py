"""
Agent Module

WHY THIS FOLDER:
In agentic AI, each agent is an independent module with:
1. Clear inputs (Pydantic schemas)
2. Clear outputs (structured JSON)
3. Single responsibility

AGENT PHILOSOPHY:
- Agents don't call each other directly
- Orchestrator (API endpoints) chains them
- Each agent can be tested in isolation

UPCOMING AGENTS:
- resume_parser.py
- job_analyzer.py
- skill_matcher.py
- scorer.py
- feedback.py
"""
