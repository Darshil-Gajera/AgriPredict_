# AgriPredict — Complete Setup & Deployment Guide

## Local Development Setup

### 1. Clone and configure
```bash
git clone <your-repo>
cd agripredict
cp .env.example .env
# Edit .env with your real values
```

### 2. Django setup
```bash
cd django_app
pip install -r ../requirements.txt
python manage.py migrate
python manage.py seed_data          # loads all 31 colleges + 10 scholarships
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py runserver          # runs on http://127.0.0.1:8000
```

### 3. Build RAG vector store (first time)
```bash
cd ../chatbot_api
# Copy your PDF brochures into data/pdfs/
# The sample cutoffs CSV is already in data/cutoffs/
python services/ingest.py           # builds FAISS index in data/vector_store/
```

### 4. Start FastAPI chatbot
```bash
cd chatbot_api
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
# Health check: http://127.0.0.1:8001/health/
```

### 5. Start Celery worker (for emails/SMS)
```bash
cd django_app
celery -A agripredict worker -l info
```

---

## PythonAnywhere Deployment

PythonAnywhere's free tier runs one WSGI app. The FastAPI chatbot needs
a paid account (or a separate free account). Recommended approach:

### Option A — Free tier (Django only, no chatbot)
1. Upload project via Git or zip
2. Set `CHATBOT_API_URL=` (empty) in .env — chat widget auto-hides
3. Use the WSGI config in `docs/pythonanywhere_wsgi.py`
4. Add a scheduled task: `python manage.py clearsessions` (weekly)

### Option B — Paid tier (Django + FastAPI)
1. Deploy Django on the main WSGI app
2. Run FastAPI in a separate bash console as a background process:
   ```bash
   cd ~/agripredict/chatbot_api && uvicorn main:app --port 8001 &
   ```
3. Set `CHATBOT_API_URL=http://127.0.0.1:8001` in .env

### PythonAnywhere steps:
```
1. Web tab → Add new web app → Manual configuration → Python 3.10
2. WSGI file → paste content of docs/pythonanywhere_wsgi.py
3. Static files:
   URL: /static/   Directory: /home/gajera06/agripredict/django_app/staticfiles
   URL: /media/    Directory: /home/gajera06/agripredict/media
4. Virtualenv → /home/gajera06/.virtualenvs/agripredict
5. Reload web app
```

### Database (Production)
For production, switch from SQLite to PostgreSQL:
```
DATABASE_URL=postgres://user:password@host:5432/agripredict
```
PythonAnywhere provides MySQL on free tier — adjust DATABASE_URL accordingly:
```
DATABASE_URL=mysql://gajera06:password@gajera06.mysql.pythonanywhere-services.com/gajera06$agripredict
```

---

## Adding Cutoff Data

### Via Admin Panel
1. Go to `/admin/` → Colleges → Cutoff Merits → Add
2. Select course, year, round, category, and enter last merit score

### Via CSV import (bulk)
Place CSV file in `chatbot_api/data/cutoffs/` with columns:
`college_code, college_name, course, year, round, student_category, last_merit`

Then rebuild the RAG index:
```bash
curl -X POST http://localhost:8001/chat/rebuild-index \
  -H "Content-Type: application/json" \
  -d '{"secret": "your-ingest-secret"}'
```

---

## Adding Gujarati Translations

### For model data (colleges, scholarships, notifications)
Use the Django Admin — each model shows EN and GU tabs.

### For UI strings
```bash
cd django_app
django-admin makemessages -l gu -i "env/*"
# Edit locale/gu/LC_MESSAGES/django.po
django-admin compilemessages
```

---

## Project Structure Summary

```
agripredict/
├── .env.example              ← Copy to .env and fill values
├── requirements.txt          ← All Python dependencies
├── django_app/
│   ├── manage.py
│   ├── agripredict/          ← Django project config
│   │   ├── settings/
│   │   │   ├── base.py       ← Main settings
│   │   │   ├── dev.py        ← Development overrides
│   │   │   └── prod.py       ← Production overrides
│   │   ├── urls.py
│   │   ├── celery.py
│   │   └── templates/
│   │       └── base.html     ← Master template with navbar + chat widget
│   ├── accounts/             ← Custom user, saved results
│   ├── predict/              ← Merit calculator (all 3 categories)
│   │   └── merit.py          ← Pure Python merit engine
│   ├── colleges/             ← All 31 colleges + cutoff data
│   │   └── fixtures/colleges.json
│   ├── notifications/        ← Official notifications + admission dates
│   ├── scholarships/         ← 10 scholarships (EN + GU)
│   │   └── fixtures/scholarships.json
│   └── core/                 ← Home, FAQ, Contact, Admission Guide
│       ├── tasks.py          ← Celery: email + SMS notifications
│       ├── fixtures/faq.json ← FAQ in EN + GU
│       └── management/commands/seed_data.py
├── chatbot_api/
│   ├── main.py               ← FastAPI app
│   ├── config.py             ← Settings via pydantic-settings
│   ├── routers/
│   │   ├── chat.py           ← POST /chat/ endpoint
│   │   └── health.py         ← GET /health/
│   ├── services/
│   │   ├── ingest.py         ← PDF + CSV + MD → FAISS
│   │   └── rag_chain.py      ← LangChain RAG + Gemini
│   ├── models/schemas.py     ← Pydantic request/response models
│   └── data/
│       ├── pdfs/             ← Drop college brochures here
│       ├── cutoffs/
│       │   └── cutoffs_2024.csv
│       └── faq/
│           └── agripredict_faq.md
└── docs/
    ├── pythonanywhere_wsgi.py
    └── SETUP.md              ← This file
```
