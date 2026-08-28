# Sync server stub for Minimal Habit Tracker

This small Express server acts as a secure proxy for GitHub Contents API operations so the browser client does not need to hold a Personal Access Token.

Usage (development)

1. Create a GitHub personal access token with `repo` scope and set it as an environment variable:

   export SERVER_PAT=ghp_...

2. Install deps:

   npm install

3. Run:

   npm start

4. The client expects POST /api/backup with JSON body:
   - Get remote: { action: "get", owner, repo, path }
     -> returns { exists, sha?, content? }
   - Put remote: { action: "put", owner, repo, path, content, sha?, message? }
     -> returns GitHub response

Security notes

- DO NOT commit `SERVER_PAT` to the repository.
- For production, implement OAuth or GitHub App flow to authorize per-user access and store tokens securely.
