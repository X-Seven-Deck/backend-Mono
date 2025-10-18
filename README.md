# X-sevenAI: Enterprise-Grade Business Automation Platform

## Overview

X-sevenAI is a scalable business automation platform with AI-powered chat systems, microservices architecture, and enterprise-grade security. The platform integrates 9 microservices, AI orchestration, real-time chats, and Supabase for authentication and database management.

## Features

- **AI-Powered Chat Systems**: Dedicated Chat, Dashboard AI Chat, and Global Chat
- **Multiple Entry Points**: Web/Mobile, QR Codes, WhatsApp, Instagram/Facebook, Voice/WebRTC, API
- **Microservices Architecture**: 9 independent services for scalability and maintainability
- **Enterprise-Grade Security**: Zero-trust with mTLS, RBAC, and end-to-end encryption
- **Global Scalability**: Auto-scaling with Kubernetes, multi-region failover
- **Real-Time Analytics**: Dashboards for business insights and performance metrics

## Tech Stack

- **Backend**: FastAPI, Supabase
- **AI & ML**: LangGraph, Temporal, Crew AI, DSPy
- **Communication**: WebRTC, ElevenLabs, Whisper
- **Infrastructure**: Docker, Kubernetes, Terraform
- **Messaging & Events**: Kafka
- **Monitoring**: Prometheus, Grafana
- **Integration**: Zapier

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.10+
- Node.js 18+
- AWS or GCP account (for production deployment)

### Local Development Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/x7AI.git
   cd x7AI
   ```

2. Copy the environment variables template:

   ```bash
   cp .env.example .env
   ```

3. Update the `.env` file with your credentials.

4. Start the development environment:

   ```bash
   docker-compose up -d
   ```

5. Access the services:
   - API Gateway: <http://localhost:8000>
   - Auth Service: <http://localhost:8010>
   - Monitoring Dashboard: <http://localhost:3000>

## Project Structure

```text
x7ai/
├── docs/                          # Documentation files
├── infra/                         # Infrastructure as Code
│   ├── kubernetes/                # K8s manifests
│   ├── docker/                    # Docker configurations
│   ├── terraform/                 # Cloud provisioning
│   └── monitoring/                # Prometheus/Grafana configs
├── scripts/                       # Automation scripts
├── shared/                        # Shared libraries and utilities
├── services/                      # All 9 microservices
│   ├── api-gateway/
│   ├── auth-service/
│   └── ...
├── .github/                       # GitHub Actions for CI/CD
└── README.md                      # This file
```

## Development Workflow

1. Create a feature branch from `main`
2. Implement your changes
3. Write tests for your code
4. Submit a pull request
5. CI/CD pipeline will run tests and linting
6. After approval, changes will be merged to `main`

## Deployment

### Staging

```bash
./scripts/deploy.sh staging
```

### Production

```bash
./scripts/deploy.sh production
```

## Documentation

For more detailed information, see the documentation in the `docs/` directory:

- [Vision and Overview](docs/visionx7.md)
- [Microservices Architecture](docs/micorstcuture.md)
- [Frameworks and Tools](docs/framework.md)
- [Entry Points](docs/entrypoint.md)
- [Folder Structure](docs/folderstructure.md)
- [Production Plan](docs/plan.md)

## License

Proprietary - All Rights Reserved

## Contact

For questions or support, contact [your-email@example.com](mailto:your-email@example.com)
