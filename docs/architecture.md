# Architecture Overview

## System Components

### Frontend (Next.js 14)
- **App Router**: File-system based routing under `app/`
- **Route groups**: `(auth)` for unauthenticated pages, `(dashboard)` for protected pages
- **State**: React context for auth state, React Query (Phase 3+) for server state
- **Design system**: shadcn/ui components built on Radix UI primitives
- **API communication**: Axios client with JWT Bearer token injection

### Backend (FastAPI)
- **Versioned API**: All routes prefixed `/api/v1/`
- **Layered architecture**: Routes → Services → Repository → DB
- **Async**: Full async/await stack using asyncpg and SQLAlchemy 2.0 async
- **Background jobs**: Celery tasks for long-running scan operations
- **Middleware stack**: CORS, rate limiting, request ID, secure headers

### Database (PostgreSQL 16)
- **ORM**: SQLAlchemy 2.0 with Mapped[] declarative style
- **Migrations**: Alembic with autogenerate support
- **UUIDs**: All primary keys are UUIDs (uuid-ossp extension)
- **Timestamps**: All records have created_at/updated_at

### Queue (Redis + Celery)
- Redis DB 0: Celery broker
- Redis DB 1: Celery result backend
- Queues: `scans` (scan jobs), `default` (other async work)
- Worker concurrency: 4 (production), 2 (development)

---

## Scanner Architecture

```
POST /api/v1/scans
        │
        ▼
  ScanService.create_scan()
        │
        ▼
  celery_app.send_task('run_scan', scan_id)
        │
        ▼
  ScanWorker.run_scan(scan_id)
        │
        ├──── WebsiteScanner.execute()
        ├──── SecretsScanner.execute()
        └──── DependencyScanner.execute()
                │
                ▼
         ScanResult (raw)
                │
                ▼
        FindingNormalizer.normalize()
                │
                ▼
        RiskEngine.score()
                │
                ▼
        FindingService.create_findings()
                │
                ▼
        [Optional] AIService.analyze()
```

Each scanner implements the `BaseScanner` abstract interface:
```python
class BaseScanner(ABC):
    @abstractmethod
    async def execute(self, asset: Asset, scan: Scan) -> ScanResult: ...
    
    @abstractmethod
    def normalize_results(self, raw: ScanResult) -> list[NormalizedFinding]: ...
    
    @property
    @abstractmethod
    def scanner_name(self) -> str: ...
    
    @property
    @abstractmethod
    def supported_asset_types(self) -> list[AssetType]: ...
```

---

## Security Architecture

### Request Lifecycle

```
Client Request
    │
    ▼
Nginx (rate limit, headers, TLS termination)
    │
    ▼
FastAPI (CORS check)
    │
    ▼
JWT Middleware (token validation)
    │
    ▼
Role Authorization (RBAC check)
    │
    ▼
Request Validation (Pydantic)
    │
    ▼
Service Layer (business logic)
    │
    ▼
Database (parameterized queries)
    │
    ▼
Response (serialized, no secrets)
```

### SSRF Prevention Model

```
URL submitted for scanning
    │
    ▼
Asset lookup (must be registered in DB)
    │
    ▼
Authorization confirmed? (DB flag)
    │
    ▼
URL scheme validation (https/http only)
    │
    ▼
Hostname validation (no localhost, no internal)
    │
    ▼
DNS resolution check (result must be public IP)
    │
    ▼
Private IP range block (RFC 1918, loopback, etc.)
    │
    ▼
Cloud metadata endpoint block (169.254.169.254, etc.)
    │
    ▼
HTTP request with timeout + size limit
```

---

## Data Models

See [database documentation](./database.md) for full schema.

Core relationships:

```
User
 └── owns → Project(s)
               └── has → Asset(s)
               └── has → Scan(s)
                           └── produces → Finding(s)
                                           └── has → AIAnalysis
               └── has → Report(s)

AuditLog → references User + Resource
```

---

## AI Service Abstraction

The AI layer is provider-agnostic. Adding a new AI provider requires only implementing the `AIProvider` interface:

```python
class AIProvider(ABC):
    @abstractmethod
    async def analyze_finding(self, context: FindingContext) -> AIAnalysisResult: ...
    
    @abstractmethod
    async def chat(self, messages: list[ChatMessage], project_context: ProjectContext) -> str: ...
```

Current implementations: `OpenAIProvider`, `AnthropicProvider`

Configured via `AI_PROVIDER` environment variable.

---

## Logging Strategy

All logs use structured JSON format in production.

Log levels:
- `DEBUG`: Development detail (disabled in production)
- `INFO`: Normal operations, request completions
- `WARNING`: Degraded state, recoverable errors
- `ERROR`: Operation failure, requires attention
- `CRITICAL`: System failure

Never logged:
- Passwords
- JWT tokens (not even partial)
- API keys
- User credentials
- Full secrets values
