Convert the research pipeline notebook into a production-ready FastAPI app with SSE streaming, deployed via Railway from GitHub.

What to build:
app/main.py → FastAPI, CORS, GET /health, POST /research (SSE)

app/pipeline.py → async generator yielding stage events

app/models.py → ResearchRequest + FinalReport models

Procfile, railway.toml, requirements.txt

Key details:
Reuse same agents from notebook

Unique SQLiteSession per request (uuid-based)

API keys loaded from environment

Ready to git push and auto-deploy on Railway.
