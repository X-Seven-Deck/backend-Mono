# Folder Structure for X-sevenAI Microservices

## Overview

X-sevenAI follows a clean, scalable folder structure designed for enterprise-grade microservices development. The project is organized into a monorepo with separate directories for each of the 9 microservices, shared infrastructure, documentation, and tooling. This structure promotes modularity, CI/CD integration, and easy deployment via Docker/Kubernetes. Each microservice is self-contained with its own codebase, dependencies, and configurations, while shared components ensure consistency.

## Root Directory Structure

```
x-sevenai/
├── docs/                          # Documentation files
│   ├── visionx7.md                # Platform vision and overview
│   ├── microstructure.md          # Microservices architecture
│   ├── framework.md               # Frameworks and tools
│   ├── entrypoint.md              # Entry points
│   └── folderstructure.md         # This file
├── infra/                         # Infrastructure as Code
│   ├── kubernetes/                # K8s manifests for all services
│   ├── docker/                    # Docker Compose for local dev
│   ├── terraform/                 # Cloud provisioning
│   └── monitoring/                # Prometheus/Grafana configs
├── scripts/                       # Automation scripts
│   ├── build.sh                   # Build all services
│   ├── deploy.sh                  # Deploy to staging/prod
│   └── test.sh                    # Run all tests
├── shared/                        # Shared libraries and utilities
│   ├── libs/                      # Common Python modules (e.g., auth helpers)
│   ├── configs/                   # Shared config files (e.g., logging)
│   └── schemas/                   # API schemas (OpenAPI)
├── services/                      # All 9 microservices
│   ├── api-gateway/
│   ├── auth-service/
│   ├── business-logic-service/
│   ├── ai-orchestration-service/
│   ├── chat-communication-service/
│   ├── analytics-dashboard-service/
│   ├── notification-integration-service/
│   ├── monitoring-logging-service/
│   └── global-chat-service/
├── .github/                       # GitHub Actions for CI/CD
├── .env.example                   # Environment variables template
├── docker-compose.yml             # Local development setup
├── requirements.txt               # Shared dependencies (if any)
├── pyproject.toml                 # Python project config
└── README.md                      # Project overview
```

## Microservice Folder Structure

Each microservice in `services/` follows a consistent, clean structure for maintainability and scalability. This ensures every service can be developed, tested, and deployed independently. Below is the full structure with explanations for each folder and file, including why it's necessary and its role in enterprise-grade development.

### Full Microservice Structure

```
services/{service-name}/
├── app/                           # Core application code directory
│   ├── __init__.py                # Python package initializer; makes the directory a module
│   ├── main.py                    # FastAPI application entry point; defines the app instance and routes
│   ├── routes/                    # API endpoint definitions
│   │   ├── __init__.py            # Package init for routes
│   │   ├── auth.py                # Authentication-related endpoints (e.g., login/logout)
│   │   └── business.py            # Business-specific endpoints (e.g., CRUD for orders)
│   ├── models/                    # Data models using Pydantic
│   │   └── user.py                # Example: User model for validation and serialization
│   ├── services/                  # Business logic layer, separate from routes
│   │   └── order_service.py       # Example: Logic for processing orders
│   ├── utils/                     # Utility functions and helpers
│   │   └── helpers.py             # Common functions like date formatting
│   └── config/                    # Configuration management
│       └── settings.py            # App settings, loaded from environment variables
├── tests/                         # Test suite for unit and integration tests
│   ├── __init__.py                # Test package init
│   ├── test_routes.py             # Tests for API routes
│   ├── test_services.py           # Tests for business logic
│   └── conftest.py                # Pytest fixtures and shared test setup
├── migrations/                    # Database schema changes (if using ORM like Alembic)
│   └── 001_initial.py             # Example: Initial DB migration
├── docker/                        # Docker configuration
│   ├── Dockerfile                 # Instructions to build the service container
│   └── .dockerignore              # Files to exclude from Docker build context
├── k8s/                           # Kubernetes deployment manifests
│   ├── deployment.yaml            # Defines pods, replicas, and containers
│   ├── service.yaml               # Exposes the service within the cluster
│   └── configmap.yaml             # External configuration (e.g., env vars)
├── requirements.txt               # Python dependencies specific to this service
├── .env                           # Local environment variables (gitignored for security)
├── pytest.ini                     # Pytest configuration (e.g., coverage settings)
├── Makefile                       # Automation scripts for build, test, run
└── README.md                      # Service-specific documentation
```

### Detailed Explanations for Each Folder/File

#### app/ (Core Application Code)
- **Why?** Contains all source code for the microservice, ensuring clean separation of concerns. This is the heart of the service, where logic is implemented.
- **Key Benefits**: Allows independent development; easy to navigate and maintain. Follows MVC-like structure for readability.
- **Enterprise Role**: Supports scalability by isolating code changes; enables code reviews and testing.

#### app/__init__.py
- **Why?** Marks the directory as a Python package, allowing imports.
- **Enterprise Role**: Standard practice for modular code; prevents import errors.

#### app/main.py
- **Why?** Entry point for the FastAPI app, including startup logic and global middleware.
- **Enterprise Role**: Centralized app definition for consistency; includes health checks and logging setup.

#### app/routes/
- **Why?** Groups API endpoints for organization; each file handles related routes (e.g., auth vs. business).
- **Enterprise Role**: Improves maintainability; allows role-based access control per route group.

#### app/models/
- **Why?** Defines data structures with validation; ensures data integrity.
- **Enterprise Role**: Prevents invalid data; supports API documentation via OpenAPI.

#### app/services/
- **Why?** Contains business logic, decoupled from routes for reusability.
- **Enterprise Role**: Enables testing of logic independently; supports complex workflows.

#### app/utils/
- **Why?** Stores reusable helpers to avoid code duplication.
- **Enterprise Role**: Promotes DRY principles; centralizes common functions like encryption.

#### app/config/
- **Why?** Manages settings from env vars or files; avoids hardcoding.
- **Enterprise Role**: Supports multi-environment configs (dev/staging/prod); enhances security.

#### tests/
- **Why?** Houses all tests to ensure quality and prevent regressions.
- **Enterprise Role**: Enables CI/CD with automated testing; critical for reliability in production.

#### migrations/
- **Why?** Tracks DB schema changes; essential if the service interacts with databases.
- **Enterprise Role**: Ensures DB consistency across environments; version-controlled for rollbacks.

#### docker/
- **Why?** Defines containerization for consistent deployment.
- **Enterprise Role**: Supports microservices portability; integrates with K8s for scaling.

#### k8s/
- **Why?** Contains manifests for K8s deployment.
- **Enterprise Role**: Enables auto-scaling, load balancing, and self-healing in production.

#### requirements.txt
- **Why?** Lists dependencies for reproducible installs.
- **Enterprise Role**: Prevents version conflicts; audited for security vulnerabilities.

#### .env
- **Why?** Stores sensitive vars locally; never committed to git.
- **Enterprise Role**: Protects secrets; uses tools like Vault for production.

#### pytest.ini
- **Why?** Configures test runner for coverage and reporting.
- **Enterprise Role**: Ensures high test coverage; integrates with CI for quality gates.

#### Makefile
- **Why?** Provides shortcuts for common tasks (e.g., `make test`).
- **Enterprise Role**: Speeds up development; standardizes commands across teams.

#### README.md
- **Why?** Documents the service's purpose, setup, and usage.
- **Enterprise Role**: Onboards new developers; includes API docs and troubleshooting.

This structure is applied to all 9 microservices (API Gateway, Auth Service, etc.), ensuring consistency and scalability.

## Detailed Explanation by Microservice

### 1. API Gateway Service (`services/api-gateway/`)
   - **Purpose**: Centralized routing, security, and entry point handling.
   - **Key Folders**: `routes/` for gateway logic; `config/` for Kong/Traefik configs; `tests/` for routing tests.
   - **Explanation**: Acts as the front door, so includes webhooks for entry points (e.g., WhatsApp). Uses shared libs for auth validation.

### 2. Authentication & User Management Service (`services/auth-service/`)
   - **Purpose**: User auth, profiles, and OAuth.
   - **Key Folders**: `models/` for user schemas; `services/` for JWT/OAuth logic; `migrations/` for Supabase DB changes.
   - **Explanation**: Self-contained for security; integrates with shared auth helpers.

### 3. Business Logic Service (`services/business-logic-service/`)
   - **Purpose**: Orders, reservations, menus.
   - **Key Folders**: `services/` for Temporal workflows; `routes/` for CRUD APIs; `tests/` for transaction tests.
   - **Explanation**: Core logic isolated; uses Kafka for events to other services.

### 4. AI Orchestration Service (`services/ai-orchestration-service/`)
   - **Purpose**: AI workflows, prompts, LLMs.
   - **Key Folders**: `services/` for LangGraph/Crew AI; `models/` for AI data; `utils/` for DSPy optimizations.
   - **Explanation**: AI-heavy; includes GPU configs in Docker for inference.

### 5. Chat & Communication Service (`services/chat-communication-service/`)
   - **Purpose**: Real-time chats, voice, messaging.
   - **Key Folders**: `routes/` for WebSocket endpoints; `services/` for ElevenLabs/Whisper; `utils/` for message queuing.
   - **Explanation**: High-concurrency; uses Redis for session caching.

### 6. Analytics & Dashboard Service (`services/analytics-dashboard-service/`)
   - **Purpose**: Data aggregation, reports, visualizations.
   - **Key Folders**: `services/` for Kafka consumers; `models/` for analytics schemas; `routes/` for dashboard APIs.
   - **Explanation**: Read-heavy; integrates with Grafana for external dashboards.

### 7. Notification & Integration Service (`services/notification-integration-service/`)
   - **Purpose**: Outbound notifications, third-party integrations.
   - **Key Folders**: `services/` for Twilio/Zapier; `routes/` for webhook handlers; `utils/` for retry logic.
   - **Explanation**: Event-driven; focuses on reliability for external APIs.

### 8. Infrastructure Monitoring & Logging Service (`services/monitoring-logging-service/`)
   - **Purpose**: Metrics, logs, observability.
   - **Key Folders**: `config/` for Prometheus/Grafana; `services/` for log aggregation; `k8s/` for cluster monitoring.
   - **Explanation**: Observes all services; uses shared schemas for consistent metrics.

### 9. Global Chat Service (`services/global-chat-service/`)
   - **Purpose**: Universal AI chatbot for cross-business interactions.
   - **Key Folders**: `services/` for Crew AI agents; `routes/` for chat APIs; `models/` for conversation data.
   - **Explanation**: Integrates with Supabase for DB queries; uses Temporal for reservations.

## Best Practices and Explanations
- **Consistency**: All services use the same structure for easy onboarding of developers.
- **Separation**: Shared code (e.g., auth) goes in `shared/libs/` to avoid duplication.
- **Scalability**: Docker/K8s folders enable containerized, orchestrated deployments.
- **Security**: `.env` files are gitignored; use secrets management in K8s.
- **CI/CD**: GitHub Actions in `.github/` automate builds/tests for each service.
- **Local Dev**: `docker-compose.yml` spins up all services for testing.

This structure ensures X-sevenAI is maintainable, scalable, and enterprise-ready. Clone the repo and follow the READMEs for setup.

---

*X-sevenAI: Clean, Scalable Microservices Architecture.*
