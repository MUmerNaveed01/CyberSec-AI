# AI Cybersecurity Assessment Platform

A professional, production-oriented cybersecurity assessment platform engineered for authorized, defensive vulnerability analysis across web applications, source code, and software dependency manifests.

---

## 🌟 Key Capabilities

- **🔐 Robust Authentication & RBAC**: Argon2id password hashing, JWT access/refresh token rotation, role-based access control (`ADMIN`, `ANALYST`, `VIEWER`).
- **📁 Projects & Asset Workspaces**: Multi-tenant assessment projects with automated security score calculation.
- **🛡️ Mandatory Authorization Gate**: Strictly requires explicit user ownership/testing certification prior to running scans.
- **🌐 Website Security Scanner**: Automated assessment of HTTPS enforcement, TLS/HSTS, Content Security Policy (CSP), X-Frame-Options, X-Content-Type-Options, cookie security flags (`Secure`), and server fingerprint banners.
- **🚫 SSRF Protection Engine**: Comprehensive pre-validation of target URLs blocking loopback (`127.0.0.1`), RFC 1918 private subnets, and cloud metadata endpoints (`169.254.169.254`).
- **🔑 Secrets Detection Scanner**: Shannon-entropy pattern recognition for AWS keys, API tokens, database connection URIs, and private RSA/SSH keys with automatic masking (`************A91F`).
- **📦 Dependency Vulnerability Scanner**: Manifest parsing (`package.json`, `requirements.txt`) with vulnerability CVE mapping and remediation recommendations.
- **📊 Standardized Risk Engine**: Unified finding schema with deterministic risk scoring (0.1 to 10.0 scale).
- **🤖 AI Security Analyst**: Structured finding explanations, business impact evaluations, and prioritized remediation plans.
- **📄 Security Reporting Engine**: On-demand generation and export of Executive and Technical assessment reports.
- **⚡ Next.js 14 Dark SaaS UI**: Responsive, professional cybersecurity dashboard with interactive charts and real-time state management.

---

## 🏗️ Architecture & Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Next.js 14, React 18, TypeScript, Tailwind CSS, shadcn/ui, Recharts, React Hook Form, Zod |
| **Backend** | FastAPI, Python 3.12, Async SQLAlchemy 2.0, Pydantic v2, Passlib (Argon2id), PyJWT |
| **Database** | PostgreSQL 16 with UUID & pg_stat extensions, Alembic Migrations |
| **Workers & Cache** | Redis 7.2, Celery 5.4 |
| **Reverse Proxy** | Nginx 1.25 with rate-limiting zones and security headers |
| **Containers** | Multi-stage Dockerfiles, Docker Compose |

---

## 🚀 Getting Started

### 1. Environment Setup

Copy `.env.example` and customize your configuration:

```bash
cp .env.example .env
```

### 2. Launch Services with Docker Compose

Start all services (PostgreSQL, Redis, FastAPI backend, Celery worker, Next.js frontend, and Nginx reverse proxy):

```bash
docker compose up --build -d
```

### 3. Apply Database Migrations

```bash
docker compose exec backend alembic upgrade head
```

### 4. Access the Application

- **Web Console**: `http://localhost:3000` (or `http://localhost` via Nginx)
- **API Documentation**: `http://localhost:8000/docs`
- **Health Endpoint**: `http://localhost:8000/api/v1/health`

---

## 🧪 Testing

Execute the automated test suite covering authentication, RBAC, projects, assets, scanning pipelines, AI analysis, and reporting:

```bash
cd backend
pytest -v
```

---

## 📜 Ethical & Defensive Security Notice

This platform is strictly designed for **authorized, defensive security assessments**. It does not perform destructive exploitation, credential brute-forcing, or denial-of-service attacks. Testing against unauthorized third-party systems is prohibited.
