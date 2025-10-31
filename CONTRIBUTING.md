# Contributing to Axon Pharmacy

Thank you for your interest in contributing. This document outlines how to set up the project, propose changes, and submit pull requests in a consistent, secure way.

## Table of Contents
- Project Setup
- Branching and Commits
- Code Style and Quality
- Secrets and Configuration
- Running the Apps
- Testing
- Submitting a Pull Request
- Reporting Issues and Feature Requests

## Project Setup
1. Fork the repository and clone your fork:
   ```bash
   git clone https://github.com/<your-username>/axon-pharma.git
   cd axon-pharma
   ```
2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate     # Windows
   # or
   source .venv/bin/activate   # macOS/Linux
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Branching and Commits
- Create a feature branch per change:
  ```bash
  git checkout -b feat/<short-name>
  # or for fixes
  git checkout -b fix/<short-name>
  ```
- Write clear commit messages using conventional style when possible:
  - feat: add guest mode restrictions to order actions
  - fix: initialize Firebase projectId for Streamlit Cloud
  - docs: update README with live app link

## Code Style and Quality
- Prefer clear, readable Python code with descriptive names.
- Keep control flow simple; use early returns where appropriate.
- Add concise comments only when non-obvious decisions or invariants exist.
- Do not introduce linter/type errors. If your editor flags issues, fix them before committing.

## Secrets and Configuration
Never commit real secrets.
- Local development: create a `.env` with placeholders:
  ```env
  GEMINI_API_KEY=...
  TELEGRAM_BOT_TOKEN=...
  ```
- Streamlit Cloud: use the Secrets UI. Example for Firebase service account:
  ```toml
  [FIREBASE_CREDENTIALS]
  type = "service_account"
  project_id = "your-project-id"
  private_key_id = "..."
  private_key = """
  -----BEGIN PRIVATE KEY-----
  ...
  -----END PRIVATE KEY-----
  """
  client_email = "..."
  token_uri = "https://oauth2.googleapis.com/token"
  ```
- Optional explicit project id:
  ```toml
  FIREBASE_PROJECT_ID = "your-project-id"
  ```

## Running the Apps
- User app:
  ```bash
  streamlit run app.py
  ```
- Admin app:
  ```bash
  streamlit run admin.py
  ```

## Testing
- Add unit tests under `tests/` where feasible. Prefer small, focused tests for pure functions.
- For features touching Firebase, isolate logic and mock external calls when possible.

## Submitting a Pull Request
1. Ensure your branch is up to date with `main`:
   ```bash
   git fetch origin
   git rebase origin/main
   ```
2. Run the app(s) locally to verify changes.
3. Push your branch and open a Pull Request against `main`:
   - Provide a concise description of the problem and solution.
   - Include screenshots or terminal output when relevant.
   - List any follow-ups or known limitations.

## Reporting Issues and Feature Requests
- Use clear, actionable titles.
- Include reproduction steps, expected vs actual behavior, and environment details.
- For feature requests, describe the user story and acceptance criteria.

Thanks for helping improve Axon Pharmacy.
