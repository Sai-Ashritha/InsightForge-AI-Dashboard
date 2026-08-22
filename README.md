# AI Predictive Manufacturing Dashboard

A free and beginner-friendly business intelligence and predictive analytics project for manufacturing and business decision making.

## Tech stack
- React
- FastAPI
- Python
- Pandas
- Scikit-learn
- Plotly
- PostgreSQL
- VS Code
- GitHub

## Project goal
This project analyzes manufacturing and business data to provide:
- KPI dashboards
- sales forecasting
- inventory insights
- anomaly detection
- business recommendations
- AI-powered explanation layer

## Run backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Run frontend
```bash
cd frontend
npm install
npm run dev
```

## Run the full stack with Docker
Install Docker Desktop, copy `.env.example` to `.env`, set a strong `JWT_SECRET_KEY`, then run:

```bash
docker compose up --build
```

The dashboard is available at `http://localhost:3000` and the API at `http://localhost:8000/docs`.
PostgreSQL runs in the `insightforge_db` service and persists data in the `postgres_data` volume.

## Authentication
Create a user with `POST /api/auth/register`, then exchange the email and password for a JWT at `POST /api/auth/token` using OAuth2 form fields (`username` and `password`).

Protected routes:
- `POST /api/upload`: requires `admin` or `analyst`
- `POST /api/chat`: requires any active authenticated user
- `GET /api/auth/me`: requires any active authenticated user

The dashboard and read-only analytics endpoints remain public for monitoring use cases.

## Local AI and BI integrations
The streaming assistant uses Ollama when available and falls back to the local rule-based insight engine when it is offline:

```bash
ollama pull llama3.2
```

Set `OLLAMA_URL` and `OLLAMA_MODEL` in `.env` as needed. The streaming endpoint is `POST /api/chat/stream`.

The dashboard's BI Report panel reads `VITE_BI_REPORT_URL`. Point it at a self-hosted Metabase or Apache Superset dashboard, for example:

```bash
VITE_BI_REPORT_URL=http://localhost:3001
```

No paid service is required; the report panel remains optional when no BI server is running.

Machine-learning endpoints:
- `GET /api/ml/forecast`: authenticated 30-day Random Forest forecast
- `GET /api/ml/anomalies`: authenticated Isolation Forest results
- `GET /api/ml/inventory`: authenticated low-stock correlation

## Backend tests
```bash
cd backend
pytest tests -q
```

## Future modules
- Data upload
- Quality checks
- Data cleaning
- ML forecasting
- AI chatbot
- Power BI integration
