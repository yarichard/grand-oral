## Grand oral topic selection

For a global description please see:
@README.md

### Technical stack
- Always use uv for Python package management, never use pip
- When adding a package in pyproject.toml, alway ensure to recompute requirements.txt with the command `uv pip compile pyproject.toml -o requirements.txt`
- App has 2 versions: one notebook for prototype purpose, and the Python module for production application, that can be pushed to Hugging Face

