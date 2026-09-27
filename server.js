const express = require('express');
const fetch = globalThis.fetch || require('node-fetch');
const bodyParser = require('body-parser');

const app = express();
app.use(bodyParser.json());

// Use a server-side PAT or implement per-user OAuth.
// STORE THIS SECRET OUTSIDE SOURCE CODE (env var, secret manager).
const SERVER_PAT = process.env.SERVER_PAT;
if (!SERVER_PAT) {
  console.warn('SERVER_PAT not set — GitHub API calls will fail until SERVER_PAT is provided.');
}

const makeGhHeaders = () => ({
  Authorization: `token ${SERVER_PAT}`,
  Accept: 'application/vnd.github.v3+json',
  'Content-Type': 'application/json'
});

// POST /api/backup
// Body: { action: "get"|"put", owner, repo, path, content?, sha?, message? }
// GET returns { exists, sha?, content? }
// PUT returns the GitHub response (or error)
app.post('/api/backup', async (req, res) => {
  const { action, owner, repo, path, content, sha, message } = req.body || {};
  if (!owner || !repo || !path || !action) return res.status(400).json({ error: 'owner, repo, path and action required' });

  const apiUrl = `https://api.github.com/repos/${owner}/${repo}/contents/${encodeURIComponent(path)}`;

  try {
    if (action === 'get') {
      const r = await fetch(apiUrl, { headers: makeGhHeaders() });
      if (r.status === 404) return res.json({ exists: false });
      const j = await r.json();
      // decode base64 if content exists
      let contentParsed = null;
      if (j.content) {
        try {
          const buff = Buffer.from(j.content, 'base64').toString('utf8');
          contentParsed = JSON.parse(buff);
        } catch (e) {
          contentParsed = null;
        }
      }
      return res.json({ exists: true, sha: j.sha, content: contentParsed, raw: j });
    }

    if (action === 'put') {
      if (typeof content !== 'string') return res.status(400).json({ error: 'content (string) required for put' });
      const body = { message: message || 'Update habit backup', content: Buffer.from(content, 'utf8').toString('base64') };
      if (sha) body.sha = sha;
      const r = await fetch(apiUrl, { method: 'PUT', headers: makeGhHeaders(), body: JSON.stringify(body) });
      const j = await r.json();
      if (!r.ok) return res.status(r.status).json(j);
      return res.json(j);
    }

    return res.status(400).json({ error: 'unknown action' });
  } catch (err) {
    console.error('api/backup error', err);
    return res.status(500).json({ error: err.message || String(err) });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`sync server stub listening on ${PORT}`));
