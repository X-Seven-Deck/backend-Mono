# Business Logic Service

To run the business logic service:

```bash
cd services/business-logic-service
source .venv/bin/activate
uvicorn app.main:app --reload --port 8030