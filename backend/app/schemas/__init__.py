"""
Pydantic Schemas

WHY THIS FOLDER:
Schemas define the "contract" between agents.

EXAMPLE:
- Resume Parser Agent outputs → ResumeSchema
- Job Analyzer Agent outputs → JobRequirementsSchema
- Skill Matcher takes BOTH as input

BENEFITS:
- Type safety (Python catches errors before runtime)
- Auto-validation (invalid data rejected immediately)
- Auto-documentation (FastAPI generates OpenAPI spec)

In interviews, explain:
"We use Pydantic schemas so agents can't pass malformed data to each other."
"""
