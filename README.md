# CareerGuide India 🎓

> **AI-Powered One-Stop Career & Education Advisor for Class 10 & 12 Students**

An open, multilingual platform that helps rural and government-school students choose streams, degrees, colleges, and career paths using ensemble ML — entirely free.

---

## Quick Start (Local Development)

### Prerequisites
- Python 3.12+
- Git
- Docker & Docker Compose (for containerized run)
- Redis (optional for Celery — skip for basic dev)

### 1. Clone & Setup

```bash
git clone https://github.com/your-org/Personalized-Career-and-Education-Advisor.git
cd Personalized-Career-and-Education-Advisor

# Copy environment variables
cp .env.example .env
# Edit .env with your keys (Supabase, Google Maps, etc.)
```

### 2. Install Python Dependencies

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-dev.txt  # for testing
```

### 3. Initialize Database

```bash
# For local SQLite (no config needed)
flask --app run:app db init
flask --app run:app db migrate -m "Initial migration"
flask --app run:app db upgrade

# For Supabase PostgreSQL: set DATABASE_URL in .env, then run the same commands
# Also run: docs/schema.sql in Supabase SQL Editor
```

### 4. Train the ML Model

```bash
# Generate synthetic training dataset (1200 students)
python scripts/generate_dataset.py

# Train ensemble model (~2-5 minutes)
python scripts/train_model.py

# Artifacts saved to: app/ml/artifacts/
```

### 5. Seed Sample Data

```bash
python scripts/seed_db.py
```

### 6. Run Development Server

```bash
python run.py
# Open: http://localhost:5000
```

---

## Docker (Production-like)

```bash
# Build and start all services
docker-compose up --build

# Access at: http://localhost:80

# Run migrations in container
docker-compose exec web flask --app run:app db upgrade

# Train ML model in container
docker-compose exec web python scripts/train_model.py
```

---

## Project Structure

```
app/
├── __init__.py          # Application factory
├── config.py            # Environment-based config
├── extensions.py        # Flask extension singletons
├── models/              # SQLAlchemy ORM models
├── repositories/        # Data access layer (queries)
├── services/            # Business logic
├── ml/                  # ML pipeline + inference
│   ├── pipeline.py      # Feature preprocessing
│   ├── ensemble.py      # Stacking ensemble model
│   ├── inference.py     # Flask-consumable inference
│   └── artifacts/       # Trained .pkl files
├── routes/              # Flask blueprints (8 modules)
├── templates/           # Jinja2 HTML templates
├── static/              # CSS, JS, images
└── utils/               # Validators, decorators, i18n

scripts/
├── generate_dataset.py  # Synthetic data generator
├── train_model.py       # Model training pipeline
└── seed_db.py           # Database seed script

docs/
├── schema.sql           # Supabase PostgreSQL schema + RLS
├── api.md               # REST API reference
├── architecture.md      # System architecture (Mermaid)
└── deployment.md        # Deployment guide
```

---

## Key Features

| Feature | Status |
|---|---|
| Student onboarding (4-step wizard) | ✅ |
| Aptitude quiz (56 questions, 6 sections) | ✅ |
| ML ensemble recommendation (RF+XGBoost+LR) | ✅ |
| SHAP-based explainability | ✅ |
| College map explorer (Google Maps) | ✅ |
| Career roadmap visualization | ✅ |
| Scholarship matching engine | ✅ |
| Multi-channel notifications (Email/SMS/WhatsApp) | ✅ |
| Admin + counselor dashboards | ✅ |
| Role-based access control | ✅ |
| Multilingual (EN/TA/HI scaffold) | ✅ |
| Dark mode UI + GSAP animations | ✅ |
| Docker + CI/CD | ✅ |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET/POST | `/auth/register` | User registration |
| GET/POST | `/auth/login` | Login |
| GET/POST | `/student/onboarding` | 4-step onboarding wizard |
| GET | `/student/quiz` | Aptitude quiz |
| POST | `/student/quiz/submit` | Submit quiz answers |
| GET | `/recommendations/dashboard` | View recommendations |
| POST | `/recommendations/api/feedback` | Submit acceptance feedback |
| GET | `/colleges/map` | College map view |
| GET | `/colleges/api/search` | Search colleges API |
| GET | `/analytics/api/impact` | Platform impact stats |
| GET | `/admin/dashboard` | Admin analytics (admin only) |

---

## Environment Variables

See [`.env.example`](.env.example) for all required variables.

**Minimum required for local dev:**
```
FLASK_SECRET_KEY=any-random-string
# Everything else has sensible defaults (SQLite, no email, etc.)
```

---

## Running Tests

```bash
pytest tests/ -v --cov=app
```

---

## Deployment

See [`docs/deployment.md`](docs/deployment.md) for:
- Render.com one-click deploy
- Railway.app setup
- AWS/GCP production setup
- Nginx + Gunicorn configuration

---

## Revenue Model

See [`docs/revenue_model.md`](docs/revenue_model.md) for B2G/B2B monetization strategy, district licensing model, and placement pitch.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python Flask 3.0 (blueprint architecture) |
| Database | SQLAlchemy + PostgreSQL (Supabase) |
| Auth | Flask-Login + Supabase JWT |
| ML | scikit-learn + XGBoost + SHAP |
| Frontend | Jinja2 + Tailwind CSS + GSAP |
| Maps | Google Maps JS API |
| Notifications | SendGrid + Twilio |
| Queue | Celery + Redis |
| Container | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Proxy | Nginx + Gunicorn |
| Observability | Sentry + structlog |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Run tests: `pytest tests/`
4. Lint: `ruff check . && black --check .`
5. Submit a Pull Request to `develop`

---

## License

MIT License — Free for educational and government use.

---

*Built with ❤️ for students who deserve better career guidance.*
