# ABDM Hospital System - PowerPoint Presentation Outline

## 📊 Generated Presentation: `/app/ABDM_System_Presentation.pptx`

---

## Slide 1: Title Slide
**ABDM Hospital System**
Ayushman Bharat Digital Mission - Healthcare Data Exchange Platform

---

## Slide 2: Problem Statement
- India's healthcare system has fragmented patient data across hospitals
- Patients struggle to access their complete medical history from multiple providers
- No standardized way to share health records between healthcare facilities
- Lack of patient consent management for health data sharing
- Need for secure, interoperable health information exchange
- **Target Users:** Hospitals, Clinics, Patients, Healthcare Providers

---

## Slide 3: High-Level Architecture
```
Hospital 1 (ABCD Hospital)          Hospital 2 (XYZ Hospital)
    Port: 8080                           Port: 8081
    Role: HIU                            Role: HIP
    Bridge: hiu-001                      Bridge: hip-002
           |                                   |
           |          GATEWAY (Port 8000)      |
           |          ├─ Authentication        |
           |          ├─ Bridge Management     |
           |          ├─ Consent Management    |
           |          └─ Data Transfer         |
           |___________________________________|
```
**HIP** = Health Information Provider | **HIU** = Health Information User

---

## Slide 4: Technology Stack

### Backend Stack
- Python 3.8+
- FastAPI (Modern async web framework)
- SQLAlchemy ORM
- SQLite Database
- Pydantic (Data validation)
- JWT Authentication
- Uvicorn ASGI Server

### Frontend & Patterns
- HTML5 / CSS3 / JavaScript
- REST API Architecture
- Async/Await Patterns
- HTTPX (Async HTTP client)
- Loguru (Logging)
- python-dotenv (Config)
- UUID for unique IDs

---

## Slide 5: Codebase Structure
```
/app/
├── abdm-gateway/                  # Central ABDM Gateway Service
│   ├── app/
│   │   ├── api/routes/            # Endpoint handlers
│   │   ├── core/                  # Config, security, logging
│   │   ├── deps/                  # Auth, headers dependencies
│   │   ├── services/              # Business logic
│   │   └── main.py                # FastAPI entry
│
├── abdm-hospital/                 # Hospital 1 (HIU Role)
│   ├── app/                       # Backend application
│   ├── frontend/                  # Web UI
│   └── *.db                       # SQLite databases
│
├── abdm-hospital-2/               # Hospital 2 (HIP Role)
```

---

## Slide 6: Module Responsibilities

### Gateway Components
- `api/routes/` - REST endpoints
- `api/schemas/` - Request/Response models
- `core/config.py` - Environment settings
- `core/security.py` - JWT handling
- `deps/auth.py` - Auth middleware
- `deps/headers.py` - ABDM headers

### Services Layer
- `auth_service.py` - Token management
- `bridge_service.py` - Bridge operations
- `consent_service.py` - Consent flow
- `data_service.py` - Health data transfer
- `linking_service.py` - Patient linking

---

## Slide 7: Core Features - ABDM Gateway
- **Authentication Service:** Client credentials, JWT token generation
- **Bridge Management:** Register hospitals, update webhooks, manage services
- **Patient Linking:** Link discovery, OTP verification, care context linking
- **Consent Management:** Initialize, track status, fetch consent artefacts
- **Data Transfer:** Request health info, send records, track delivery status
- Centralized routing between HIP and HIU

---

## Slide 8: Core Features - Hospital System
- **Patient Management:** Register, search, view patient profiles
- **Visit Management:** OPD/IPD tracking, department-wise visits
- **Care Context:** Group related health episodes for a patient
- **Health Records:** Prescriptions, Diagnostic Reports, Lab Results
- **Gateway Integration:** Auth sessions, bridge registration, webhooks
- **Frontend Dashboard:** Real-time patient data visualization

---

## Slide 9: Data Flow Diagram
```
Hospital 1 (HIU)                                    Hospital 2 (HIP)
     │                                                    │
     │  1. Request Patient Data                           │
     ├──────────────────┐                                 │
     │                  ▼                                 │
     │          ┌─────────────┐                           │
     │          │   GATEWAY   │  2. Validate Consent      │
     │          │             │  3. Forward Request       │
     │          │  Consent    │────────────────────────────►
     │          │  Validator  │                           │
     │          │             │  4. Fetch Records         │
     │          │  Data       │◄────────────────────────────
     │          │  Router     │  5. Return Health Data    │
     │          └─────────────┘                           │
     │                  │                                 │
     │◄─────────────────┘                                 │
     │  6. Deliver Records                                │
     ▼                                                    │
[Store in DB]
```

---

## Slide 10: Gateway API Endpoints

### Authentication & Bridge
- `POST /api/auth/session` - Get token
- `POST /api/bridge/register` - Register bridge
- `PATCH /api/bridge/url` - Update webhook
- `GET /api/bridge/{id}/services` - List services
- `POST /api/link/token/generate` - Link token
- `POST /api/link/carecontext` - Link contexts

### Linking & Data Transfer
- `POST /api/link/discover` - Find patient
- `POST /api/link/init` - Initialize linking
- `POST /api/link/confirm` - Confirm with OTP
- `POST /api/consent/init` - Start consent
- `GET /api/consent/status/{id}` - Get status
- `POST /api/data/request` - Request data

---

## Slide 11: Database Schema
```
PATIENTS                    VISITS                    CARE_CONTEXTS
├─ id (UUID, PK)           ├─ id (UUID, PK)          ├─ id (UUID, PK)
├─ name (String)           ├─ patient_id (FK)        ├─ patient_id (FK)
├─ mobile (String, UQ)     ├─ visit_type (String)    ├─ context_name (String)
├─ abha_id (String, UQ)    ├─ department (String)    └─ description (String)
└─ aadhaar (String, UQ)    ├─ doctor_id (String)
                           ├─ visit_date (DateTime)
HEALTH_RECORDS             └─ status (String)
├─ id (UUID, PK)
├─ patient_id (FK)
├─ record_type (String)
├─ record_date (DateTime)
├─ data_json (JSON)
├─ source_hospital (String)
└─ was_encrypted (Boolean)
```

---

## Slide 12: Key Design Decisions
- **Microservices Architecture:** Separate gateway and hospital services
- **Repository Pattern:** Clean separation of data access and business logic
- **In-Memory Storage (Gateway):** Fast prototyping with Dict-based stores
- **SQLite Database (Hospital):** Lightweight, file-based persistence
- **JWT-based Authentication:** Stateless, scalable token verification
- **Async/Await:** Non-blocking I/O for high concurrency
- **CORS Middleware:** Enable secure cross-origin requests

---

## Slide 13: Architectural Patterns Used
- **REST API Design:** Resource-based endpoints, proper HTTP methods
- **Dependency Injection:** FastAPI's Depends() for auth and headers
- **Service Layer Pattern:** Business logic in dedicated service modules
- **Gateway Pattern:** Centralized routing and protocol translation
- **Webhook Pattern:** Event-driven communication between hospitals
- **Token Manager Pattern:** Centralized credential and token handling
- **Factory Pattern:** Pydantic models for request/response creation

---

## Slide 14: Security & Performance Considerations
- JWT Token Authentication with configurable expiry (default: 15 min)
- Client Credentials Grant for machine-to-machine communication
- CORS Configuration: Whitelist trusted origins only
- Request ID & Timestamp Headers for audit trail
- X-CM-ID Header for multi-tenant support
- Environment-based secrets (JWT_SECRET in .env)
- Consent-based data access: Verify consent before data transfer

---

## Slide 15: Setup & Deployment
1. **Prerequisites:** Python 3.8+, pip, virtual environment
2. Clone repository and create virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Configure `.env` files with credentials and URLs
5. Initialize database: `python init_db.py`
6. Start services using uvicorn on ports 8000, 8080, 8081
7. API Documentation available at `/docs` (Swagger UI)

---

## Slide 16: Running Commands
```bash
# Terminal 1: Start ABDM Gateway
cd abdm-gateway
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2: Start Hospital 1
cd abdm-hospital
python init_db.py
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8080

# Terminal 3: Start Hospital 2
cd abdm-hospital-2
python init_db.py
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8081

# Verify Health
curl http://localhost:8000/health
curl http://localhost:8080/health
curl http://localhost:8081/health
```

---

## Slide 17: Future Enhancements
- **Scalability:** Move to PostgreSQL, add Redis caching
- **Real ABDM Integration:** Connect to national ABDM sandbox/production
- **Encryption:** Implement end-to-end encryption for health data
- **Kubernetes Deployment:** Containerize services for cloud deployment
- **Audit Logging:** Comprehensive logging for compliance (HIPAA, GDPR)
- **Real-time Notifications:** WebSocket for instant consent updates
- **Mobile App:** Patient-facing mobile application for consent management

---

## Slide 18: Summary
- ABDM Hospital System enables secure health data exchange
- Three-tier architecture: Gateway + Multiple Hospitals
- Built with modern Python stack (FastAPI, SQLAlchemy, Pydantic)
- Implements ABDM-compliant flows: Linking, Consent, Data Transfer
- Production-ready patterns with JWT auth and consent validation
- Comprehensive documentation and test suite included
- Foundation for national health information exchange

---

## Slide 19: Thank You!
Questions?

---

## 📁 Files Generated
- **PowerPoint Presentation:** `/app/ABDM_System_Presentation.pptx` (55 KB, 19 slides)
- **Outline Document:** `/app/PRESENTATION_OUTLINE.md`
- **Generator Script:** `/app/generate_presentation.py`

---

*Generated on: August 2025*
