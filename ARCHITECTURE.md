# ReconForge – Architektur-Dokument

> **Version:** 1.0  
> **Datum:** 22. Februar 2026  
> **Status:** Entwurf  
> **Zielgruppe:** Entwicklungsteam, Pentesting-Team, Projektleitung

---

## Inhaltsverzeichnis

1. [Projektübersicht](#1-projektübersicht)
2. [Systemarchitektur](#2-systemarchitektur)
3. [Tech-Stack](#3-tech-stack)
4. [Monorepo-Struktur](#4-monorepo-struktur)
5. [Datenmodell](#5-datenmodell)
6. [Tool-Integration Layer](#6-tool-integration-layer)
7. [Scan-Orchestrator & Pipeline-Engine](#7-scan-orchestrator--pipeline-engine)
8. [Chain Logic – Intelligente Verkettung](#8-chain-logic--intelligente-verkettung)
9. [API-Design](#9-api-design)
10. [Frontend-Architektur](#10-frontend-architektur)
11. [Authentifizierung & Autorisierung](#11-authentifizierung--autorisierung)
12. [Sicherheit & DSGVO](#12-sicherheit--dsgvo)
13. [Reporting-Engine](#13-reporting-engine)
14. [Deployment & Infrastruktur](#14-deployment--infrastruktur)
15. [Epics & Roadmap](#15-epics--roadmap)
16. [Anhang: Tool-Referenz](#16-anhang-tool-referenz)

---

## 1. Projektübersicht

### 1.1 Vision

ReconForge ist ein internes Reconnaissance-Orchestrierungstool für Pentesting-Teams, das die Aufklärungsphase bei externen Kundenengagements von mehreren Stunden auf Minuten reduziert. Es orchestriert 18+ Open-Source-Sicherheitstools in einer automatisierten Pipeline, aggregiert Ergebnisse in einer zentralen Datenbank und liefert priorisierte, kundenfertige Reports.

### 1.2 Kernziele

- **Zeitersparnis:** Automatisierte Reconnaissance reduziert manuelle Arbeit um 60–80%
- **Qualitätssicherung:** Die Pipeline vergisst nichts – konsistente Ergebnisse unabhängig vom Erfahrungslevel des Pentesters
- **Zusammenarbeit:** Mehrere Pentester arbeiten gleichzeitig an einem Projekt, sehen Ergebnisse in Echtzeit
- **Nachvollziehbarkeit:** Vollständiges Audit-Log für jede Aktion, rechtlich belastbar
- **Kundenmehrwert:** Scan-Historie ermöglicht Fortschrittsvergleiche über Zeit

### 1.3 Anwendungsfall

Primär: Pentesting für externe Kunden. Das Tool deckt den gesamten Reconnaissance-Workflow ab:

1. Scope-Definition und rechtliche Absicherung
2. Passive Aufklärung (OSINT, Subdomain-Enumeration)
3. Aktives Scanning (Ports, Services, Web-Schwachstellen)
4. Ergebnis-Aggregation und Priorisierung
5. Reporting und Kundenübergabe

### 1.4 Nicht-Ziele (Out of Scope)

- Kein Ersatz für manuelle Exploitation (Metasploit bleibt ein Hilfstool, kein Autopilot)
- Keine SaaS-Lösung – ausschließlich On-Premise
- Kein Bug-Bounty-Plattform-Ersatz

---

## 2. Systemarchitektur

### 2.1 Architekturdiagramm

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (SPA)                       │
│  Dashboard · Scan-Konfig · Ergebnis-Explorer · Reporting     │
│  Team-Mgmt · Scope-Mgmt · Scan-Historie · Activity Feed     │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST API (JSON) + WebSocket (Live-Updates)
                       │ HTTPS / TLS 1.3
┌──────────────────────┴──────────────────────────────────────┐
│                  Python Backend (FastAPI)                     │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────┐  │
│  │ Auth &   │ │ Project  │ │ Scan      │ │ Reporting    │  │
│  │ RBAC     │ │ Manager  │ │ Orchestra-│ │ Engine       │  │
│  │ Module   │ │          │ │ tor       │ │ (WeasyPrint) │  │
│  └──────────┘ └──────────┘ └─────┬─────┘ └──────────────┘  │
│                                   │                          │
│  ┌────────────────────────────────┴────────────────────┐    │
│  │           Tool-Integration Layer (Wrapper)           │    │
│  │  ┌─────┐ ┌────────┐ ┌─────┐ ┌──────┐ ┌──────────┐  │    │
│  │  │nmap │ │recon-ng│ │nikto│ │sqlmap│ │metasploit│  │    │
│  │  └─────┘ └────────┘ └─────┘ └──────┘ └──────────┘  │    │
│  │  ┌──────┐ ┌─────────┐ ┌────┐ ┌───┐ ┌────────┐     │    │
│  │  │nuclei│ │subfinder│ │httpx│ │ffuf│ │impacket│     │    │
│  │  └──────┘ └─────────┘ └────┘ └───┘ └────────┘     │    │
│  │  ┌──────┐ ┌──────┐ ┌─────┐ ┌────────────┐          │    │
│  │  │sslyze│ │wpscan│ │hydra│ │theHarvester│  ...     │    │
│  │  └──────┘ └──────┘ └─────┘ └────────────┘          │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────┴───────┐ ┌────┴────┐ ┌──────┴──────┐
│  PostgreSQL   │ │  Redis  │ │ Filesystem  │
│  (Daten +     │ │ (Queue +│ │ (Scan-      │
│   Audit-Log)  │ │  Cache) │ │  Artefakte) │
└───────────────┘ └─────────┘ └─────────────┘
```

### 2.2 Komponentenübersicht

| Komponente | Verantwortlichkeit |
|------------|-------------------|
| **React Frontend** | Benutzeroberfläche, Echtzeit-Updates, Scan-Konfiguration, Reporting-UI |
| **FastAPI Backend** | Geschäftslogik, API-Endpunkte, WebSocket-Server, Authentifizierung |
| **Scan-Orchestrator** | Pipeline-Steuerung, Chain Logic, Job-Scheduling |
| **Tool-Integration Layer** | Einheitliche Wrapper für alle externen Tools |
| **Celery Workers** | Asynchrone Ausführung von Scan-Jobs |
| **PostgreSQL** | Persistente Datenhaltung, Audit-Log, Scan-Historie |
| **Redis** | Message-Broker für Celery, Cache, WebSocket-Pub/Sub |
| **Filesystem** | Rohe Tool-Outputs, Report-PDFs, Scope-Dokumente |

### 2.3 Kommunikationsfluss

```
User → Frontend → REST API → Backend → Celery Task Queue → Worker
                                                              │
                                                    Tool-Wrapper ausführen
                                                              │
                                                    Ergebnis normalisieren
                                                              │
                                                    In PostgreSQL speichern
                                                              │
                                              WebSocket Event → Frontend (Live)
```

---

## 3. Tech-Stack

### 3.1 Backend

| Technologie | Version | Zweck |
|------------|---------|-------|
| **Python** | 3.12+ | Hauptsprache Backend |
| **FastAPI** | 0.110+ | REST API + WebSocket-Server |
| **Celery** | 5.4+ | Asynchrone Task-Queue |
| **SQLAlchemy** | 2.0+ | ORM / Datenbankzugriff |
| **Alembic** | 1.13+ | Datenbank-Migrationen |
| **Pydantic** | 2.0+ | Datenvalidierung & Serialisierung |
| **WeasyPrint** | 62+ | HTML → PDF Report-Generierung |
| **python-jose** | 3.3+ | JWT-Token-Handling |
| **passlib[bcrypt]** | 1.7+ | Passwort-Hashing |
| **uvicorn** | 0.30+ | ASGI-Server |

### 3.2 Frontend

| Technologie | Version | Zweck |
|------------|---------|-------|
| **React** | 18+ | UI-Framework |
| **TypeScript** | 5.0+ | Typsicherheit |
| **Vite** | 5+ | Build-Tool & Dev-Server |
| **Tailwind CSS** | 3.4+ | Styling |
| **React Router** | 6+ | Routing |
| **TanStack Query** | 5+ | Server-State-Management |
| **Zustand** | 4+ | Client-State-Management |
| **Recharts** | 2+ | Visualisierungen / Charts |
| **React Flow** | 11+ | Netzwerk-Topologie-Darstellung |

### 3.3 Infrastruktur

| Technologie | Version | Zweck |
|------------|---------|-------|
| **PostgreSQL** | 16+ | Hauptdatenbank |
| **Redis** | 7+ | Message-Broker + Cache |
| **Docker** | 25+ | Containerisierung |
| **Docker Compose** | 2.24+ | Multi-Container-Orchestrierung |
| **Nginx** | 1.25+ | Reverse Proxy + Static File Serving |
| **Certbot** | 2+ | TLS-Zertifikatsverwaltung |

---

## 4. Monorepo-Struktur

```
reconforge/
├── README.md
├── ARCHITECTURE.md              ← Dieses Dokument
├── docker-compose.yml           ← Gesamtes Stack-Setup
├── docker-compose.dev.yml       ← Entwicklungs-Overrides
├── .env.example                 ← Umgebungsvariablen-Template
├── .gitignore
├── Makefile                     ← Convenience-Commands
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml           ← Python-Dependencies (Poetry/uv)
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/            ← DB-Migrationen
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              ← FastAPI App-Instanz
│   │   ├── config.py            ← Settings (Pydantic BaseSettings)
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py          ← Dependency Injection
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py    ← Haupt-Router
│   │   │   │   ├── auth.py
│   │   │   │   ├── projects.py
│   │   │   │   ├── scans.py
│   │   │   │   ├── findings.py
│   │   │   │   ├── reports.py
│   │   │   │   ├── users.py
│   │   │   │   └── websocket.py
│   │   │   └── middleware/
│   │   │       ├── audit.py     ← Audit-Logging Middleware
│   │   │       └── rate_limit.py
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py      ← JWT, Hashing, Encryption
│   │   │   ├── database.py      ← SQLAlchemy Engine/Session
│   │   │   └── events.py        ← WebSocket Event Manager
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── scope.py
│   │   │   ├── scan.py
│   │   │   ├── finding.py
│   │   │   ├── audit_log.py
│   │   │   └── report.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── user.py          ← Pydantic Request/Response Schemas
│   │   │   ├── project.py
│   │   │   ├── scan.py
│   │   │   ├── finding.py
│   │   │   └── report.py
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── project_service.py
│   │   │   ├── scan_service.py
│   │   │   ├── finding_service.py
│   │   │   ├── report_service.py
│   │   │   └── scope_validator.py
│   │   │
│   │   ├── orchestrator/
│   │   │   ├── __init__.py
│   │   │   ├── engine.py        ← Pipeline-Engine
│   │   │   ├── chain_logic.py   ← Intelligente Verkettung
│   │   │   ├── profiles.py      ← Scan-Profile (Quick/Standard/Deep)
│   │   │   └── scheduler.py     ← Job-Scheduling
│   │   │
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── base.py          ← Abstrakte Basisklasse ToolWrapper
│   │   │   ├── result.py        ← Einheitliches Ergebnis-Format
│   │   │   │
│   │   │   ├── recon/           ← OSINT & Discovery Tools
│   │   │   │   ├── __init__.py
│   │   │   │   ├── subfinder.py
│   │   │   │   ├── amass.py
│   │   │   │   ├── recon_ng.py
│   │   │   │   ├── theharvester.py
│   │   │   │   ├── httpx.py
│   │   │   │   ├── dnsx.py
│   │   │   │   └── whatweb.py
│   │   │   │
│   │   │   ├── scanning/        ← Aktive Scanner
│   │   │   │   ├── __init__.py
│   │   │   │   ├── nmap.py
│   │   │   │   ├── nuclei.py
│   │   │   │   ├── nikto.py
│   │   │   │   ├── ffuf.py
│   │   │   │   └── wpscan.py
│   │   │   │
│   │   │   ├── exploitation/    ← Validierung & Exploit-Check
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sqlmap.py
│   │   │   │   ├── metasploit.py
│   │   │   │   ├── hydra.py
│   │   │   │   └── impacket_wrapper.py
│   │   │   │
│   │   │   ├── web_analysis/    ← Web-spezifische Analyse
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sslyze.py
│   │   │   │   ├── arjun.py
│   │   │   │   ├── linkfinder.py
│   │   │   │   └── secretfinder.py
│   │   │   │
│   │   │   └── infrastructure/  ← Netzwerk & AD
│   │   │       ├── __init__.py
│   │   │       ├── enum4linux.py
│   │   │       └── bloodhound.py
│   │   │
│   │   └── reporting/
│   │       ├── __init__.py
│   │       ├── generator.py     ← Report-Generierung
│   │       ├── templates/       ← HTML/CSS Report-Templates
│   │       │   ├── executive_summary.html
│   │       │   ├── technical_report.html
│   │       │   └── styles.css
│   │       └── exporters/
│   │           ├── pdf.py
│   │           ├── html.py
│   │           └── json_export.py
│   │
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── celery_app.py        ← Celery-Konfiguration
│   │   └── tasks/
│   │       ├── __init__.py
│   │       ├── scan_tasks.py    ← Scan-bezogene Celery Tasks
│   │       └── report_tasks.py  ← Report-Generierung Tasks
│   │
│   └── tests/
│       ├── conftest.py
│       ├── test_api/
│       ├── test_tools/
│       ├── test_orchestrator/
│       └── test_services/
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── index.html
│   │
│   ├── public/
│   │   └── favicon.svg
│   │
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── routes.tsx
│       │
│       ├── api/
│       │   ├── client.ts         ← Axios/Fetch-Client mit Auth-Interceptor
│       │   ├── websocket.ts      ← WebSocket-Client
│       │   ├── projects.ts
│       │   ├── scans.ts
│       │   ├── findings.ts
│       │   └── reports.ts
│       │
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Sidebar.tsx
│       │   │   ├── Header.tsx
│       │   │   └── MainLayout.tsx
│       │   ├── common/
│       │   │   ├── Button.tsx
│       │   │   ├── Modal.tsx
│       │   │   ├── DataTable.tsx
│       │   │   └── StatusBadge.tsx
│       │   ├── scans/
│       │   │   ├── ScanConfigurator.tsx
│       │   │   ├── ScanProgress.tsx
│       │   │   ├── ScanTimeline.tsx
│       │   │   └── ProfileSelector.tsx
│       │   ├── findings/
│       │   │   ├── FindingCard.tsx
│       │   │   ├── FindingDetail.tsx
│       │   │   ├── SeverityChart.tsx
│       │   │   └── FindingFilters.tsx
│       │   ├── network/
│       │   │   └── TopologyView.tsx
│       │   └── reports/
│       │       ├── ReportBuilder.tsx
│       │       └── ReportPreview.tsx
│       │
│       ├── pages/
│       │   ├── Dashboard.tsx
│       │   ├── Projects.tsx
│       │   ├── ProjectDetail.tsx
│       │   ├── ScanView.tsx
│       │   ├── Findings.tsx
│       │   ├── Reports.tsx
│       │   ├── TeamManagement.tsx
│       │   ├── Settings.tsx
│       │   └── Login.tsx
│       │
│       ├── hooks/
│       │   ├── useAuth.ts
│       │   ├── useWebSocket.ts
│       │   ├── useScans.ts
│       │   └── useFindings.ts
│       │
│       ├── store/
│       │   ├── authStore.ts
│       │   └── scanStore.ts
│       │
│       ├── types/
│       │   ├── project.ts
│       │   ├── scan.ts
│       │   ├── finding.ts
│       │   └── user.ts
│       │
│       └── utils/
│           ├── formatters.ts
│           └── constants.ts
│
├── nginx/
│   ├── nginx.conf
│   └── ssl/                     ← TLS-Zertifikate (gitignored)
│
├── scripts/
│   ├── setup.sh                 ← Erstinstallation
│   ├── seed_db.py               ← Initialdaten (Admin-User, Standard-Profile)
│   ├── backup.sh                ← Datenbank-Backup
│   └── check_tools.sh           ← Prüft ob alle externen Tools installiert sind
│
└── docs/
    ├── api/                     ← Auto-generierte API-Docs (OpenAPI)
    ├── guides/
    │   ├── installation.md
    │   ├── user_guide.md
    │   └── developer_guide.md
    └── adr/                     ← Architecture Decision Records
        ├── 001-monorepo.md
        ├── 002-fastapi.md
        └── 003-celery.md
```

---

## 5. Datenmodell

### 5.1 Entity-Relationship-Übersicht

```
┌──────────┐     ┌──────────────┐     ┌──────────┐
│   User   │────<│ ProjectMember│>────│  Project  │
└──────────┘     └──────────────┘     └─────┬────┘
     │                                       │
     │                                 ┌─────┴────┐
     │                                 │          │
     │                            ┌────┴───┐ ┌───┴────┐
     │                            │ Scope  │ │  Scan  │
     │                            │ Target │ │        │
     │                            └────────┘ └───┬────┘
     │                                           │
     │                                     ┌─────┴─────┐
     │                                     │  ScanJob  │
     │                                     │ (pro Tool)│
     │                                     └─────┬─────┘
     │                                           │
     │           ┌───────────┐             ┌─────┴─────┐
     └──────────>│ AuditLog  │             │  Finding  │
                 └───────────┘             └─────┬─────┘
                                                 │
                                           ┌─────┴─────┐
                                           │  Comment  │
                                           └───────────┘
```

### 5.2 Tabellenstruktur (SQL-Pseudocode)

```sql
-- =============================================
-- USERS & AUTHENTICATION
-- =============================================

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    role            VARCHAR(20) NOT NULL DEFAULT 'pentester',
                    -- 'admin', 'pentester', 'viewer'
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- PROJECTS & TEAM
-- =============================================

CREATE TABLE projects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    client_name     VARCHAR(255) NOT NULL,
    description     TEXT,
    status          VARCHAR(20) DEFAULT 'active',
                    -- 'active', 'completed', 'archived'
    start_date      DATE,
    end_date        DATE,
    auto_delete_at  TIMESTAMPTZ,         -- DSGVO: automatische Löschung
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE project_members (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    role            VARCHAR(20) DEFAULT 'pentester',
                    -- 'lead', 'pentester', 'viewer'
    joined_at       TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, user_id)
);

-- =============================================
-- SCOPE MANAGEMENT
-- =============================================

CREATE TABLE scope_targets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID REFERENCES projects(id) ON DELETE CASCADE,
    target_type     VARCHAR(20) NOT NULL,
                    -- 'domain', 'ip', 'ip_range', 'url'
    target_value    VARCHAR(500) NOT NULL,
    is_excluded     BOOLEAN DEFAULT FALSE,  -- Explizit ausgeschlossene Ziele
    notes           TEXT,
    authorization_doc VARCHAR(500),          -- Pfad zum Genehmigungsdokument
    added_by        UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- SCANS & JOBS
-- =============================================

CREATE TABLE scans (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID REFERENCES projects(id) ON DELETE CASCADE,
    name            VARCHAR(255),
    profile         VARCHAR(20) DEFAULT 'standard',
                    -- 'quick', 'standard', 'deep', 'custom'
    status          VARCHAR(20) DEFAULT 'pending',
                    -- 'pending', 'running', 'paused', 'completed',
                    -- 'failed', 'cancelled'
    config          JSONB NOT NULL DEFAULT '{}',
                    -- Enthält Tool-spezifische Konfigurationsoptionen
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    started_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE scan_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id         UUID REFERENCES scans(id) ON DELETE CASCADE,
    tool_name       VARCHAR(50) NOT NULL,
                    -- 'nmap', 'nuclei', 'subfinder', etc.
    phase           VARCHAR(20) NOT NULL,
                    -- 'recon', 'discovery', 'scanning', 'exploitation'
    status          VARCHAR(20) DEFAULT 'pending',
                    -- 'pending', 'queued', 'running', 'completed',
                    -- 'failed', 'skipped'
    config          JSONB NOT NULL DEFAULT '{}',
    target          VARCHAR(500),
    celery_task_id  VARCHAR(255),         -- Referenz zum Celery Task
    raw_output_path VARCHAR(500),         -- Pfad zur rohen Tool-Ausgabe
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    duration_seconds INTEGER,
    error_message   TEXT,
    triggered_by    UUID REFERENCES scan_jobs(id),
                    -- Chain Logic: welcher Job hat diesen ausgelöst?
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- FINDINGS
-- =============================================

CREATE TABLE findings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id         UUID REFERENCES scans(id) ON DELETE CASCADE,
    scan_job_id     UUID REFERENCES scan_jobs(id) ON DELETE SET NULL,
    project_id      UUID REFERENCES projects(id) ON DELETE CASCADE,

    -- Klassifizierung
    title           VARCHAR(500) NOT NULL,
    description     TEXT,
    severity        VARCHAR(10) NOT NULL,
                    -- 'critical', 'high', 'medium', 'low', 'info'
    cvss_score      DECIMAL(3,1),         -- 0.0 - 10.0
    cvss_vector     VARCHAR(100),
    cve_id          VARCHAR(20),          -- z.B. 'CVE-2024-12345'
    cwe_id          VARCHAR(20),          -- z.B. 'CWE-89'

    -- Ziel-Informationen
    target_host     VARCHAR(500),
    target_port     INTEGER,
    target_protocol VARCHAR(10),
    target_url      VARCHAR(2000),
    target_service  VARCHAR(100),

    -- Tool-Informationen
    source_tool     VARCHAR(50) NOT NULL,
    raw_evidence    JSONB,                -- Rohdaten vom Tool

    -- Workflow-Status
    status          VARCHAR(20) DEFAULT 'open',
                    -- 'open', 'confirmed', 'false_positive',
                    -- 'accepted_risk', 'remediated'
    assigned_to     UUID REFERENCES users(id),
    verified_by     UUID REFERENCES users(id),
    verified_at     TIMESTAMPTZ,

    -- Deduplizierung
    fingerprint     VARCHAR(64),          -- SHA-256 Hash für Dedup
    is_duplicate    BOOLEAN DEFAULT FALSE,
    duplicate_of    UUID REFERENCES findings(id),

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_findings_project_severity
    ON findings(project_id, severity);
CREATE INDEX idx_findings_fingerprint
    ON findings(fingerprint);
CREATE INDEX idx_findings_status
    ON findings(status);

-- =============================================
-- KOMMENTARE
-- =============================================

CREATE TABLE finding_comments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    finding_id      UUID REFERENCES findings(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES users(id),
    content         TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- AUDIT LOG
-- =============================================

CREATE TABLE audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    action          VARCHAR(50) NOT NULL,
                    -- 'scan.started', 'scan.completed', 'finding.created',
                    -- 'project.created', 'scope.modified', 'report.generated',
                    -- 'user.login', 'user.logout', etc.
    resource_type   VARCHAR(50),
    resource_id     UUID,
    details         JSONB,               -- Zusätzliche Kontextdaten
    ip_address      INET,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_log_created
    ON audit_log(created_at DESC);
CREATE INDEX idx_audit_log_user
    ON audit_log(user_id, created_at DESC);

-- =============================================
-- REPORTS
-- =============================================

CREATE TABLE reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID REFERENCES projects(id) ON DELETE CASCADE,
    scan_id         UUID REFERENCES scans(id),
    name            VARCHAR(255) NOT NULL,
    template        VARCHAR(50) DEFAULT 'standard',
    format          VARCHAR(10) DEFAULT 'pdf',
                    -- 'pdf', 'html', 'json'
    file_path       VARCHAR(500),
    config          JSONB DEFAULT '{}',
                    -- Kundenlogo-Pfad, Farben, inkludierte Severities, etc.
    generated_by    UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- SCAN-HISTORIE (Vergleiche über Zeit)
-- =============================================

CREATE TABLE scan_comparisons (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID REFERENCES projects(id) ON DELETE CASCADE,
    scan_a_id       UUID REFERENCES scans(id),
    scan_b_id       UUID REFERENCES scans(id),
    new_findings    INTEGER DEFAULT 0,
    resolved_findings INTEGER DEFAULT 0,
    unchanged_findings INTEGER DEFAULT 0,
    comparison_data JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 5.3 Finding-Fingerprint (Deduplizierung)

Um doppelte Findings aus verschiedenen Tools zu erkennen, wird ein Fingerprint berechnet:

```python
import hashlib

def compute_finding_fingerprint(
    target_host: str,
    target_port: int | None,
    target_url: str | None,
    cve_id: str | None,
    cwe_id: str | None,
    title: str,
) -> str:
    """
    Generate a SHA-256 fingerprint for deduplication.
    Findings with the same fingerprint are considered duplicates.
    """
    components = [
        target_host or "",
        str(target_port or ""),
        target_url or "",
        cve_id or "",
        cwe_id or "",
        title.lower().strip(),
    ]
    raw = "|".join(components)
    return hashlib.sha256(raw.encode()).hexdigest()
```

---

## 6. Tool-Integration Layer

### 6.1 Abstrakte Basisklasse

Jedes Tool wird über einen einheitlichen Wrapper integriert. Die Basisklasse definiert das Interface:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import asyncio
import subprocess
import json
import logging

logger = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    RECON = "recon"
    DISCOVERY = "discovery"
    SCANNING = "scanning"
    EXPLOITATION = "exploitation"
    WEB_ANALYSIS = "web_analysis"
    INFRASTRUCTURE = "infrastructure"


class ToolStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class ToolResult:
    """Einheitliches Ergebnis-Format für alle Tools."""
    tool_name: str
    target: str
    status: ToolStatus
    raw_output: str = ""
    raw_output_path: str | None = None
    findings: list[dict[str, Any]] = field(default_factory=list)
    hosts: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0


class BaseToolWrapper(ABC):
    """
    Abstrakte Basisklasse für alle Tool-Wrapper.

    Jeder Wrapper muss implementieren:
    - name: Eindeutiger Tool-Name
    - category: Kategorie des Tools
    - build_command(): CLI-Befehl zusammenbauen
    - parse_output(): Tool-Output in ToolResult umwandeln
    - is_available(): Prüfen ob das Tool installiert ist
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Eindeutiger Tool-Name, z.B. 'nmap', 'nuclei'."""
        ...

    @property
    @abstractmethod
    def category(self) -> ToolCategory:
        """Kategorie des Tools."""
        ...

    @abstractmethod
    def build_command(self, target: str, config: dict) -> list[str]:
        """
        Erstellt den CLI-Befehl als Liste.

        Args:
            target: Das Scan-Ziel (IP, Domain, URL)
            config: Tool-spezifische Konfiguration

        Returns:
            Liste von Command-Teilen, z.B. ['nmap', '-sV', '-oX', '-', '10.0.0.1']
        """
        ...

    @abstractmethod
    def parse_output(self, raw_output: str, target: str) -> ToolResult:
        """
        Parst den rohen Tool-Output in ein einheitliches ToolResult.

        Args:
            raw_output: Roher stdout/stderr Output
            target: Das gescannte Ziel

        Returns:
            ToolResult mit normalisierten Findings
        """
        ...

    def is_available(self) -> bool:
        """Prüft ob das Tool auf dem System installiert ist."""
        try:
            subprocess.run(
                [self.name, "--version"],
                capture_output=True,
                timeout=10,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    async def run(
        self,
        target: str,
        config: dict | None = None,
        timeout: int = 3600,
        scope_targets: list[str] | None = None,
    ) -> ToolResult:
        """
        Führt das Tool aus und gibt ein normalisiertes Ergebnis zurück.

        Args:
            target: Das Scan-Ziel
            config: Tool-spezifische Konfiguration
            timeout: Maximale Laufzeit in Sekunden
            scope_targets: Erlaubte Ziele (Scope-Validierung)

        Returns:
            ToolResult
        """
        config = config or {}

        # Scope-Validierung
        if scope_targets and not self._validate_scope(target, scope_targets):
            return ToolResult(
                tool_name=self.name,
                target=target,
                status=ToolStatus.FAILED,
                errors=[f"Target '{target}' is outside defined scope"],
            )

        command = self.build_command(target, config)
        logger.info(f"[{self.name}] Executing: {' '.join(command)}")

        import time
        start_time = time.time()

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            duration = time.time() - start_time

            raw_output = stdout.decode("utf-8", errors="replace")
            result = self.parse_output(raw_output, target)
            result.duration_seconds = duration

            if process.returncode != 0 and stderr:
                result.errors.append(stderr.decode("utf-8", errors="replace"))

            return result

        except asyncio.TimeoutError:
            return ToolResult(
                tool_name=self.name,
                target=target,
                status=ToolStatus.TIMEOUT,
                errors=[f"Tool timed out after {timeout} seconds"],
                duration_seconds=timeout,
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                target=target,
                status=ToolStatus.FAILED,
                errors=[str(e)],
                duration_seconds=time.time() - start_time,
            )

    def _validate_scope(self, target: str, scope_targets: list[str]) -> bool:
        """Prüft ob das Ziel im definierten Scope liegt."""
        import ipaddress

        for scope in scope_targets:
            # Exakte Übereinstimmung (Domain oder IP)
            if target == scope:
                return True
            # Subdomain-Check
            if target.endswith(f".{scope}"):
                return True
            # IP-Range-Check
            try:
                network = ipaddress.ip_network(scope, strict=False)
                ip = ipaddress.ip_address(target)
                if ip in network:
                    return True
            except ValueError:
                continue

        return False
```

### 6.2 Beispiel-Implementierung: Nmap Wrapper

```python
import xml.etree.ElementTree as ET
from app.tools.base import BaseToolWrapper, ToolCategory, ToolResult, ToolStatus


class NmapWrapper(BaseToolWrapper):
    """Wrapper for nmap network scanner."""

    @property
    def name(self) -> str:
        return "nmap"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.DISCOVERY

    def build_command(self, target: str, config: dict) -> list[str]:
        cmd = ["nmap"]

        # Scan-Typ
        scan_type = config.get("scan_type", "service")
        if scan_type == "quick":
            cmd.extend(["-F", "-T4"])            # Top 100 Ports, schnell
        elif scan_type == "service":
            cmd.extend(["-sV", "-sC", "-T3"])    # Service-Version + Default-Scripts
        elif scan_type == "full":
            cmd.extend(["-sV", "-sC", "-p-", "-T3"])  # Alle 65535 Ports
        elif scan_type == "udp":
            cmd.extend(["-sU", "--top-ports", "100"])

        # OS Detection (optional)
        if config.get("os_detection", False):
            cmd.append("-O")

        # Output als XML (für Parsing)
        cmd.extend(["-oX", "-"])

        # Timing anpassen
        if "max_rate" in config:
            cmd.extend(["--max-rate", str(config["max_rate"])])

        cmd.append(target)
        return cmd

    def parse_output(self, raw_output: str, target: str) -> ToolResult:
        result = ToolResult(
            tool_name=self.name,
            target=target,
            status=ToolStatus.COMPLETED,
            raw_output=raw_output,
        )

        try:
            root = ET.fromstring(raw_output)
        except ET.ParseError as e:
            result.status = ToolStatus.FAILED
            result.errors.append(f"Failed to parse nmap XML: {e}")
            return result

        for host_elem in root.findall(".//host"):
            addr_elem = host_elem.find("address")
            if addr_elem is None:
                continue

            host_ip = addr_elem.get("addr", "")
            host_state = "unknown"
            status_elem = host_elem.find("status")
            if status_elem is not None:
                host_state = status_elem.get("state", "unknown")

            # OS Detection
            os_matches = []
            for osmatch in host_elem.findall(".//osmatch"):
                os_matches.append({
                    "name": osmatch.get("name", ""),
                    "accuracy": osmatch.get("accuracy", ""),
                })

            # Hostname
            hostnames = []
            for hostname in host_elem.findall(".//hostname"):
                hostnames.append(hostname.get("name", ""))

            host_data = {
                "ip": host_ip,
                "state": host_state,
                "hostnames": hostnames,
                "os_matches": os_matches,
                "ports": [],
            }

            # Ports & Services
            for port_elem in host_elem.findall(".//port"):
                port_id = port_elem.get("portid", "")
                protocol = port_elem.get("protocol", "tcp")

                state_elem = port_elem.find("state")
                port_state = state_elem.get("state", "") if state_elem is not None else ""

                service_elem = port_elem.find("service")
                service_name = ""
                service_version = ""
                service_product = ""

                if service_elem is not None:
                    service_name = service_elem.get("name", "")
                    service_product = service_elem.get("product", "")
                    service_version = service_elem.get("version", "")

                port_data = {
                    "port": int(port_id),
                    "protocol": protocol,
                    "state": port_state,
                    "service": service_name,
                    "product": service_product,
                    "version": service_version,
                }
                host_data["ports"].append(port_data)

                # Finding für jeden offenen Port mit bekanntem Service
                if port_state == "open":
                    version_str = f" {service_product} {service_version}".strip()
                    result.findings.append({
                        "title": f"Open port {port_id}/{protocol}: {service_name}{version_str}",
                        "severity": "info",
                        "target_host": host_ip,
                        "target_port": int(port_id),
                        "target_protocol": protocol,
                        "target_service": service_name,
                        "description": (
                            f"Port {port_id}/{protocol} is open running "
                            f"{service_name}{version_str} on {host_ip}"
                        ),
                        "raw_evidence": port_data,
                    })

            result.hosts.append(host_data)

        result.metadata = {
            "total_hosts": len(result.hosts),
            "total_open_ports": sum(
                len([p for p in h["ports"] if p["state"] == "open"])
                for h in result.hosts
            ),
        }

        return result
```

### 6.3 Beispiel-Implementierung: Nuclei Wrapper

```python
import json
from app.tools.base import BaseToolWrapper, ToolCategory, ToolResult, ToolStatus


NUCLEI_SEVERITY_MAP = {
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
    "info": "info",
    "unknown": "info",
}


class NucleiWrapper(BaseToolWrapper):
    """Wrapper for ProjectDiscovery Nuclei vulnerability scanner."""

    @property
    def name(self) -> str:
        return "nuclei"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.SCANNING

    def build_command(self, target: str, config: dict) -> list[str]:
        cmd = ["nuclei", "-target", target, "-jsonl", "-silent"]

        # Severity-Filter
        severities = config.get("severities", ["critical", "high", "medium"])
        cmd.extend(["-severity", ",".join(severities)])

        # Template-Tags (z.B. 'cve', 'misconfig', 'default-login')
        if "tags" in config:
            cmd.extend(["-tags", ",".join(config["tags"])])

        # Template-Ausschlüsse
        if "exclude_tags" in config:
            cmd.extend(["-exclude-tags", ",".join(config["exclude_tags"])])

        # Rate-Limiting
        rate_limit = config.get("rate_limit", 150)
        cmd.extend(["-rate-limit", str(rate_limit)])

        # Concurrency
        concurrency = config.get("concurrency", 25)
        cmd.extend(["-concurrency", str(concurrency)])

        # Timeout pro Request
        timeout = config.get("timeout", 10)
        cmd.extend(["-timeout", str(timeout)])

        return cmd

    def parse_output(self, raw_output: str, target: str) -> ToolResult:
        result = ToolResult(
            tool_name=self.name,
            target=target,
            status=ToolStatus.COMPLETED,
            raw_output=raw_output,
        )

        severity_counts = {
            "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0
        }

        for line in raw_output.strip().split("\n"):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            severity = NUCLEI_SEVERITY_MAP.get(
                data.get("info", {}).get("severity", "info"), "info"
            )
            severity_counts[severity] += 1

            finding = {
                "title": data.get("info", {}).get("name", "Unknown Finding"),
                "severity": severity,
                "target_host": data.get("host", target),
                "target_url": data.get("matched-at", ""),
                "description": data.get("info", {}).get("description", ""),
                "cve_id": self._extract_cve(data),
                "cwe_id": self._extract_cwe(data),
                "source_tool": "nuclei",
                "raw_evidence": {
                    "template_id": data.get("template-id", ""),
                    "template_url": data.get("template-url", ""),
                    "matcher_name": data.get("matcher-name", ""),
                    "extracted_results": data.get("extracted-results", []),
                    "curl_command": data.get("curl-command", ""),
                },
            }
            result.findings.append(finding)

        result.metadata = {
            "total_findings": len(result.findings),
            "severity_counts": severity_counts,
        }

        return result

    def _extract_cve(self, data: dict) -> str | None:
        """Extract CVE ID from nuclei classification data."""
        classification = data.get("info", {}).get("classification", {})
        cve_ids = classification.get("cve-id", [])
        if cve_ids and isinstance(cve_ids, list):
            return cve_ids[0]
        return None

    def _extract_cwe(self, data: dict) -> str | None:
        """Extract CWE ID from nuclei classification data."""
        classification = data.get("info", {}).get("classification", {})
        cwe_ids = classification.get("cwe-id", [])
        if cwe_ids and isinstance(cwe_ids, list):
            return cwe_ids[0]
        return None
```

### 6.4 Beispiel-Implementierung: SSLyze (Direct Python Import)

```python
from sslyze import (
    Scanner,
    ServerScanRequest,
    ServerNetworkLocation,
    ScanCommand,
)
from sslyze.errors import ServerHostnameCouldNotBeResolved

from app.tools.base import BaseToolWrapper, ToolCategory, ToolResult, ToolStatus


class SSLyzeWrapper(BaseToolWrapper):
    """
    Wrapper for SSLyze SSL/TLS scanner.

    Unlike other wrappers, SSLyze is imported as a native Python library –
    no subprocess overhead.
    """

    @property
    def name(self) -> str:
        return "sslyze"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WEB_ANALYSIS

    def build_command(self, target: str, config: dict) -> list[str]:
        # Not used – SSLyze is called via Python API
        return []

    def parse_output(self, raw_output: str, target: str) -> ToolResult:
        # Not used – results are parsed directly from Python objects
        return ToolResult(tool_name=self.name, target=target, status=ToolStatus.COMPLETED)

    def is_available(self) -> bool:
        try:
            import sslyze  # noqa: F401
            return True
        except ImportError:
            return False

    async def run(
        self,
        target: str,
        config: dict | None = None,
        timeout: int = 300,
        scope_targets: list[str] | None = None,
    ) -> ToolResult:
        """Run SSLyze scan using Python API."""
        config = config or {}
        import time

        start_time = time.time()
        result = ToolResult(
            tool_name=self.name,
            target=target,
            status=ToolStatus.COMPLETED,
        )

        try:
            # Parse target (host:port)
            if ":" in target:
                host, port_str = target.rsplit(":", 1)
                port = int(port_str)
            else:
                host = target
                port = 443

            location = ServerNetworkLocation(hostname=host, port=port)
            scan_request = ServerScanRequest(
                server_location=location,
                scan_commands={
                    ScanCommand.CERTIFICATE_INFO,
                    ScanCommand.SSL_2_0_CIPHER_SUITES,
                    ScanCommand.SSL_3_0_CIPHER_SUITES,
                    ScanCommand.TLS_1_0_CIPHER_SUITES,
                    ScanCommand.TLS_1_1_CIPHER_SUITES,
                    ScanCommand.TLS_1_2_CIPHER_SUITES,
                    ScanCommand.TLS_1_3_CIPHER_SUITES,
                    ScanCommand.HEARTBLEED,
                    ScanCommand.TLS_COMPRESSION,
                    ScanCommand.TLS_FALLBACK_SCSV,
                },
            )

            scanner = Scanner()
            scanner.queue_scans([scan_request])

            for scan_result in scanner.get_results():
                # Check for deprecated protocols
                for protocol_name, scan_cmd in [
                    ("SSLv2", ScanCommand.SSL_2_0_CIPHER_SUITES),
                    ("SSLv3", ScanCommand.SSL_3_0_CIPHER_SUITES),
                    ("TLSv1.0", ScanCommand.TLS_1_0_CIPHER_SUITES),
                    ("TLSv1.1", ScanCommand.TLS_1_1_CIPHER_SUITES),
                ]:
                    proto_result = scan_result.scan_result.__getattribute__(
                        scan_cmd.value
                    )
                    if proto_result and proto_result.result:
                        accepted = proto_result.result.accepted_cipher_suites
                        if accepted:
                            result.findings.append({
                                "title": f"Deprecated protocol {protocol_name} enabled",
                                "severity": "high" if "SSL" in protocol_name else "medium",
                                "target_host": host,
                                "target_port": port,
                                "description": (
                                    f"{protocol_name} is enabled with "
                                    f"{len(accepted)} cipher suites. "
                                    f"This protocol is deprecated and insecure."
                                ),
                                "raw_evidence": {
                                    "accepted_ciphers": [
                                        c.cipher_suite.name for c in accepted
                                    ]
                                },
                            })

                # Heartbleed check
                heartbleed = scan_result.scan_result.heartbleed
                if heartbleed and heartbleed.result:
                    if heartbleed.result.is_vulnerable_to_heartbleed:
                        result.findings.append({
                            "title": "Vulnerable to Heartbleed (CVE-2014-0160)",
                            "severity": "critical",
                            "cve_id": "CVE-2014-0160",
                            "target_host": host,
                            "target_port": port,
                            "description": (
                                "The server is vulnerable to the Heartbleed bug, "
                                "which allows remote attackers to read memory contents."
                            ),
                        })

                # Certificate info
                cert_info = scan_result.scan_result.certificate_info
                if cert_info and cert_info.result:
                    for deployment in cert_info.result.certificate_deployments:
                        leaf_cert = deployment.received_certificate_chain[0]
                        not_after = leaf_cert.not_valid_after_utc

                        from datetime import datetime, timezone
                        days_until_expiry = (not_after - datetime.now(timezone.utc)).days

                        if days_until_expiry < 0:
                            result.findings.append({
                                "title": "SSL/TLS certificate has expired",
                                "severity": "high",
                                "target_host": host,
                                "target_port": port,
                                "description": (
                                    f"Certificate expired {abs(days_until_expiry)} "
                                    f"days ago on {not_after.isoformat()}"
                                ),
                            })
                        elif days_until_expiry < 30:
                            result.findings.append({
                                "title": "SSL/TLS certificate expiring soon",
                                "severity": "medium",
                                "target_host": host,
                                "target_port": port,
                                "description": (
                                    f"Certificate expires in {days_until_expiry} days "
                                    f"on {not_after.isoformat()}"
                                ),
                            })

        except ServerHostnameCouldNotBeResolved:
            result.status = ToolStatus.FAILED
            result.errors.append(f"Hostname '{host}' could not be resolved")
        except Exception as e:
            result.status = ToolStatus.FAILED
            result.errors.append(str(e))

        result.duration_seconds = time.time() - start_time
        return result
```

### 6.5 Tool-Registry

Alle Wrapper werden zentral registriert:

```python
from app.tools.base import BaseToolWrapper
from app.tools.recon.subfinder import SubfinderWrapper
from app.tools.recon.httpx import HttpxWrapper
from app.tools.scanning.nmap import NmapWrapper
from app.tools.scanning.nuclei import NucleiWrapper
from app.tools.scanning.nikto import NiktoWrapper
from app.tools.scanning.ffuf import FfufWrapper
from app.tools.exploitation.sqlmap import SqlmapWrapper
from app.tools.web_analysis.sslyze import SSLyzeWrapper
# ... weitere Imports


class ToolRegistry:
    """Central registry for all tool wrappers."""

    def __init__(self):
        self._tools: dict[str, BaseToolWrapper] = {}

    def register(self, wrapper: BaseToolWrapper) -> None:
        self._tools[wrapper.name] = wrapper

    def get(self, name: str) -> BaseToolWrapper | None:
        return self._tools.get(name)

    def get_all(self) -> dict[str, BaseToolWrapper]:
        return self._tools.copy()

    def get_available(self) -> dict[str, BaseToolWrapper]:
        return {
            name: tool for name, tool in self._tools.items()
            if tool.is_available()
        }

    def get_by_category(self, category: str) -> list[BaseToolWrapper]:
        return [
            tool for tool in self._tools.values()
            if tool.category.value == category
        ]


def create_tool_registry() -> ToolRegistry:
    """Factory function to create a fully populated tool registry."""
    registry = ToolRegistry()

    # Welle 1 – Kern-Pipeline
    registry.register(NmapWrapper())
    registry.register(NucleiWrapper())
    registry.register(SubfinderWrapper())
    registry.register(HttpxWrapper())
    registry.register(FfufWrapper())
    registry.register(SSLyzeWrapper())

    # Bestehende Tools
    registry.register(NiktoWrapper())
    registry.register(SqlmapWrapper())
    # registry.register(ReconNgWrapper())
    # registry.register(MetasploitWrapper())

    # Welle 2 – Professionalisierung
    # registry.register(TheHarvesterWrapper())
    # registry.register(WPScanWrapper())
    # registry.register(HydraWrapper())
    # registry.register(Enum4linuxWrapper())
    # registry.register(ArjunWrapper())

    return registry
```

---

## 7. Scan-Orchestrator & Pipeline-Engine

### 7.1 Scan-Profile

```python
from dataclasses import dataclass, field


@dataclass
class ScanProfile:
    """Definition eines Scan-Profils mit aktivierten Phasen und Tools."""
    name: str
    description: str
    phases: list["ScanPhase"]
    estimated_duration_minutes: int


@dataclass
class ScanPhase:
    """Eine Phase im Scan-Ablauf."""
    name: str
    order: int
    tools: list["ToolConfig"]
    parallel: bool = True       # Tools in dieser Phase parallel ausführen
    wait_for_completion: bool = True  # Warten bis Phase fertig, bevor nächste startet


@dataclass
class ToolConfig:
    """Konfiguration eines Tools innerhalb einer Phase."""
    tool_name: str
    enabled: bool = True
    config: dict = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)  # Tool-Namen


# Vordefinierte Profile
PROFILES = {
    "quick": ScanProfile(
        name="Quick Recon",
        description="Schneller Überblick: Subdomains + Top-100-Ports + Tech-Stack",
        estimated_duration_minutes=15,
        phases=[
            ScanPhase(
                name="OSINT & Discovery",
                order=1,
                tools=[
                    ToolConfig("subfinder", config={}),
                    ToolConfig("theharvester", config={"sources": ["crtsh", "dnsdumpster"]}),
                ],
            ),
            ScanPhase(
                name="Probing",
                order=2,
                tools=[
                    ToolConfig("httpx", config={"tech_detect": True}),
                    ToolConfig("nmap", config={"scan_type": "quick"}),
                ],
            ),
        ],
    ),

    "standard": ScanProfile(
        name="Standard",
        description="Vollständiger Scan: OSINT + Portscan + Web-Vuln-Analyse",
        estimated_duration_minutes=60,
        phases=[
            ScanPhase(
                name="OSINT & Discovery",
                order=1,
                tools=[
                    ToolConfig("subfinder"),
                    ToolConfig("theharvester"),
                ],
            ),
            ScanPhase(
                name="Probing & Fingerprinting",
                order=2,
                tools=[
                    ToolConfig("httpx", config={"tech_detect": True}),
                    ToolConfig("nmap", config={"scan_type": "service"}),
                ],
            ),
            ScanPhase(
                name="Vulnerability Scanning",
                order=3,
                tools=[
                    ToolConfig("nuclei", config={"severities": ["critical", "high", "medium"]}),
                    ToolConfig("nikto"),
                    ToolConfig("sslyze"),
                ],
            ),
            ScanPhase(
                name="Web Fuzzing",
                order=4,
                tools=[
                    ToolConfig("ffuf", config={"wordlist": "common.txt"}),
                ],
            ),
        ],
    ),

    "deep": ScanProfile(
        name="Deep Dive",
        description="Tiefenanalyse: Alles + SQLi + Parameter-Discovery + Auth-Testing",
        estimated_duration_minutes=180,
        phases=[
            ScanPhase(
                name="OSINT & Discovery",
                order=1,
                tools=[
                    ToolConfig("subfinder"),
                    ToolConfig("theharvester"),
                ],
            ),
            ScanPhase(
                name="Probing & Fingerprinting",
                order=2,
                tools=[
                    ToolConfig("httpx", config={"tech_detect": True}),
                    ToolConfig("nmap", config={"scan_type": "full", "os_detection": True}),
                ],
            ),
            ScanPhase(
                name="Vulnerability Scanning",
                order=3,
                tools=[
                    ToolConfig("nuclei", config={"severities": ["critical", "high", "medium", "low"]}),
                    ToolConfig("nikto"),
                    ToolConfig("sslyze"),
                    ToolConfig("wpscan"),
                ],
            ),
            ScanPhase(
                name="Web Deep Analysis",
                order=4,
                tools=[
                    ToolConfig("ffuf", config={"wordlist": "directory-list-2.3-medium.txt"}),
                    ToolConfig("arjun"),
                    ToolConfig("linkfinder"),
                    ToolConfig("secretfinder"),
                ],
            ),
            ScanPhase(
                name="Exploitation Validation",
                order=5,
                tools=[
                    ToolConfig("sqlmap", config={"level": 3, "risk": 2}),
                    ToolConfig("hydra", config={"protocols": ["ssh", "ftp"]}),
                ],
            ),
        ],
    ),
}
```

### 7.2 Pipeline-Engine

```python
import asyncio
import logging
from uuid import UUID
from datetime import datetime, timezone

from app.tools.base import ToolRegistry, ToolStatus
from app.orchestrator.chain_logic import ChainLogicEngine
from app.core.events import WebSocketEventManager

logger = logging.getLogger(__name__)


class PipelineEngine:
    """
    Orchestriert die Ausführung von Scan-Phasen und Tools.

    Verantwortlich für:
    - Phasen-Management (sequenziell)
    - Tool-Ausführung (parallel innerhalb einer Phase)
    - Chain Logic Delegation
    - Live-Status-Updates über WebSocket
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        chain_engine: "ChainLogicEngine",
        event_manager: WebSocketEventManager,
        db_session,
    ):
        self.tools = tool_registry
        self.chain_engine = chain_engine
        self.events = event_manager
        self.db = db_session

    async def execute_scan(
        self,
        scan_id: UUID,
        profile: "ScanProfile",
        targets: list[str],
        scope_targets: list[str],
        custom_config: dict | None = None,
    ) -> None:
        """
        Führt einen kompletten Scan gemäß Profil aus.

        Args:
            scan_id: ID des Scans in der Datenbank
            profile: Gewähltes Scan-Profil
            targets: Primäre Scan-Ziele
            scope_targets: Erlaubter Scope
            custom_config: Benutzerdefinierte Überschreibungen
        """
        await self.events.emit(scan_id, "scan.started", {
            "profile": profile.name,
            "targets": targets,
        })

        # Dynamische Ziel-Liste (wird durch Chain Logic erweitert)
        discovered_targets: dict[str, set] = {
            "domains": set(targets),
            "urls": set(),
            "hosts": set(),
        }

        for phase in sorted(profile.phases, key=lambda p: p.order):
            await self.events.emit(scan_id, "phase.started", {
                "phase": phase.name,
                "order": phase.order,
            })

            # Tools für diese Phase vorbereiten
            tasks = []
            for tool_config in phase.tools:
                if not tool_config.enabled:
                    continue

                wrapper = self.tools.get(tool_config.tool_name)
                if wrapper is None or not wrapper.is_available():
                    logger.warning(f"Tool '{tool_config.tool_name}' not available, skipping")
                    continue

                # Ziele für dieses Tool bestimmen
                tool_targets = self._resolve_targets(
                    tool_config.tool_name, discovered_targets, targets
                )

                for target in tool_targets:
                    config = {**tool_config.config, **(custom_config or {})}
                    tasks.append(
                        self._execute_tool(
                            scan_id=scan_id,
                            wrapper=wrapper,
                            target=target,
                            config=config,
                            scope_targets=scope_targets,
                            phase_name=phase.name,
                        )
                    )

            # Tools parallel oder sequenziell ausführen
            if phase.parallel:
                results = await asyncio.gather(*tasks, return_exceptions=True)
            else:
                results = []
                for task in tasks:
                    result = await task
                    results.append(result)

            # Chain Logic auswerten
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Tool execution failed: {result}")
                    continue

                new_targets = await self.chain_engine.evaluate(result, discovered_targets)
                # Neue Ziele für spätere Phasen verfügbar machen
                for target_type, values in new_targets.items():
                    discovered_targets.setdefault(target_type, set()).update(values)

            await self.events.emit(scan_id, "phase.completed", {
                "phase": phase.name,
            })

        await self.events.emit(scan_id, "scan.completed", {
            "total_findings": await self._count_findings(scan_id),
        })

    async def _execute_tool(
        self,
        scan_id: UUID,
        wrapper,
        target: str,
        config: dict,
        scope_targets: list[str],
        phase_name: str,
    ):
        """Führt ein einzelnes Tool aus und speichert das Ergebnis."""

        await self.events.emit(scan_id, "tool.started", {
            "tool": wrapper.name,
            "target": target,
            "phase": phase_name,
        })

        result = await wrapper.run(
            target=target,
            config=config,
            scope_targets=scope_targets,
        )

        # Ergebnisse in DB speichern
        await self._save_scan_job(scan_id, wrapper.name, target, result, phase_name)
        await self._save_findings(scan_id, result)

        await self.events.emit(scan_id, "tool.completed", {
            "tool": wrapper.name,
            "target": target,
            "findings_count": len(result.findings),
            "status": result.status.value,
            "duration": result.duration_seconds,
        })

        return result

    def _resolve_targets(
        self,
        tool_name: str,
        discovered: dict[str, set],
        primary_targets: list[str],
    ) -> list[str]:
        """Bestimmt welche Ziele ein Tool scannen soll."""
        # URL-basierte Tools bekommen URLs
        url_tools = {"nikto", "nuclei", "ffuf", "sqlmap", "arjun", "wpscan"}
        if tool_name in url_tools and discovered.get("urls"):
            return list(discovered["urls"])

        # Host-basierte Tools bekommen IPs
        host_tools = {"nmap", "enum4linux", "hydra"}
        if tool_name in host_tools and discovered.get("hosts"):
            return list(discovered["hosts"])

        # Domain-basierte Tools bekommen Domains
        return list(discovered.get("domains", set()) or primary_targets)

    async def _save_scan_job(self, scan_id, tool_name, target, result, phase):
        """Speichert einen ScanJob in der Datenbank."""
        # Implementierung: SQLAlchemy INSERT
        pass

    async def _save_findings(self, scan_id, result):
        """Speichert Findings mit Deduplizierung."""
        # Implementierung: Fingerprint berechnen, Duplikate erkennen
        pass

    async def _count_findings(self, scan_id) -> int:
        """Zählt Findings eines Scans."""
        # Implementierung: COUNT Query
        return 0
```

---

## 8. Chain Logic – Intelligente Verkettung

### 8.1 Regelbasierte Verkettung

```python
from dataclasses import dataclass
from typing import Any
import logging

from app.tools.base import ToolResult

logger = logging.getLogger(__name__)


@dataclass
class ChainRule:
    """
    Eine Verkettungsregel: Wenn Bedingung erfüllt → Aktion auslösen.
    """
    name: str
    source_tool: str
    condition: callable     # (ToolResult) -> bool
    action: callable        # (ToolResult, discovered_targets) -> dict[str, set]
    description: str = ""


class ChainLogicEngine:
    """
    Evaluiert Scan-Ergebnisse und löst automatisch Folge-Scans aus.

    Beispiele:
    - nmap findet Port 80/443 → nikto + nuclei auf diesen Host
    - subfinder findet Subdomains → nmap auf neue Subdomains
    - nmap findet alte SSH-Version → CVE-Lookup starten
    - httpx erkennt WordPress → wpscan starten
    """

    def __init__(self):
        self.rules: list[ChainRule] = []
        self._register_default_rules()

    def _register_default_rules(self):
        """Registriert die Standard-Verkettungsregeln."""

        # Regel 1: Subdomains gefunden → zu Scan-Zielen hinzufügen
        self.rules.append(ChainRule(
            name="subdomain_to_targets",
            source_tool="subfinder",
            condition=lambda result: len(result.hosts) > 0 or any(
                "subdomain" in str(f.get("raw_evidence", {}))
                for f in result.findings
            ),
            action=self._action_add_subdomains,
            description="Gefundene Subdomains werden als neue Scan-Ziele hinzugefügt",
        ))

        # Regel 2: Webserver gefunden → URL-Liste für Web-Scanner erstellen
        self.rules.append(ChainRule(
            name="webserver_to_urls",
            source_tool="nmap",
            condition=lambda result: any(
                p.get("service") in ("http", "https", "http-proxy")
                for h in result.hosts
                for p in h.get("ports", [])
                if p.get("state") == "open"
            ),
            action=self._action_create_urls_from_nmap,
            description="Offene Web-Ports werden als URLs für Web-Scanner bereitgestellt",
        ))

        # Regel 3: httpx erkennt WordPress → WPScan aktivieren
        self.rules.append(ChainRule(
            name="wordpress_detected",
            source_tool="httpx",
            condition=lambda result: any(
                "wordpress" in str(f.get("raw_evidence", {})).lower()
                for f in result.findings
            ),
            action=self._action_flag_wordpress,
            description="WordPress erkannt → WPScan wird für dieses Ziel aktiviert",
        ))

        # Regel 4: Login-Seiten gefunden → Hydra-Ziele hinzufügen
        self.rules.append(ChainRule(
            name="login_page_found",
            source_tool="ffuf",
            condition=lambda result: any(
                any(keyword in f.get("title", "").lower()
                    for keyword in ["login", "admin", "signin", "auth"])
                for f in result.findings
            ),
            action=self._action_flag_login_pages,
            description="Login-Seiten gefunden → als Ziele für Auth-Testing markiert",
        ))

        # Regel 5: SQL-Injection-Parameter → SQLMap starten
        self.rules.append(ChainRule(
            name="sqli_parameter_found",
            source_tool="arjun",
            condition=lambda result: len(result.findings) > 0,
            action=self._action_create_sqlmap_targets,
            description="HTTP-Parameter gefunden → SQLMap-Ziele erstellt",
        ))

    async def evaluate(
        self,
        result: ToolResult,
        discovered_targets: dict[str, set],
    ) -> dict[str, set]:
        """
        Evaluiert ein Tool-Ergebnis gegen alle passenden Regeln.

        Returns:
            Neue Ziele die durch Chain Logic entdeckt wurden.
        """
        new_targets: dict[str, set] = {}

        for rule in self.rules:
            if rule.source_tool != result.tool_name:
                continue

            try:
                if rule.condition(result):
                    action_targets = rule.action(result, discovered_targets)
                    for target_type, values in action_targets.items():
                        new_targets.setdefault(target_type, set()).update(values)
                    logger.info(
                        f"Chain rule '{rule.name}' triggered: "
                        f"added {sum(len(v) for v in action_targets.values())} new targets"
                    )
            except Exception as e:
                logger.error(f"Chain rule '{rule.name}' failed: {e}")

        return new_targets

    # === Action-Methoden ===

    def _action_add_subdomains(
        self, result: ToolResult, discovered: dict
    ) -> dict[str, set]:
        """Fügt entdeckte Subdomains als neue Domains hinzu."""
        new_domains = set()
        for host in result.hosts:
            if "hostname" in host:
                new_domains.add(host["hostname"])
        for finding in result.findings:
            if target := finding.get("target_host"):
                new_domains.add(target)
        return {"domains": new_domains}

    def _action_create_urls_from_nmap(
        self, result: ToolResult, discovered: dict
    ) -> dict[str, set]:
        """Erstellt URLs aus offenen Web-Ports."""
        urls = set()
        for host in result.hosts:
            ip = host.get("ip", "")
            for port in host.get("ports", []):
                if port.get("state") != "open":
                    continue
                service = port.get("service", "")
                port_num = port.get("port", 0)

                if service in ("https", "ssl/http") or port_num == 443:
                    urls.add(f"https://{ip}:{port_num}")
                elif service in ("http", "http-proxy") or port_num in (80, 8080, 8443):
                    urls.add(f"http://{ip}:{port_num}")

        return {"urls": urls}

    def _action_flag_wordpress(
        self, result: ToolResult, discovered: dict
    ) -> dict[str, set]:
        """Markiert WordPress-Ziele für WPScan."""
        wp_urls = set()
        for finding in result.findings:
            if "wordpress" in str(finding.get("raw_evidence", {})).lower():
                if url := finding.get("target_url"):
                    wp_urls.add(url)
        return {"wordpress_targets": wp_urls}

    def _action_flag_login_pages(
        self, result: ToolResult, discovered: dict
    ) -> dict[str, set]:
        """Markiert Login-Seiten für Auth-Testing."""
        login_urls = set()
        for finding in result.findings:
            if url := finding.get("target_url"):
                login_urls.add(url)
        return {"login_targets": login_urls}

    def _action_create_sqlmap_targets(
        self, result: ToolResult, discovered: dict
    ) -> dict[str, set]:
        """Erstellt SQLMap-Ziele aus entdeckten Parametern."""
        sqli_targets = set()
        for finding in result.findings:
            if url := finding.get("target_url"):
                sqli_targets.add(url)
        return {"sqlmap_targets": sqli_targets}
```

---

## 9. API-Design

### 9.1 Endpunkte-Übersicht

```
# Authentifizierung
POST   /api/v1/auth/login              → JWT-Token erhalten
POST   /api/v1/auth/refresh            → Token erneuern
POST   /api/v1/auth/logout             → Token invalidieren

# Benutzer
GET    /api/v1/users                   → Alle Benutzer (Admin)
GET    /api/v1/users/me                → Eigenes Profil
PUT    /api/v1/users/me                → Profil bearbeiten
POST   /api/v1/users                   → Benutzer anlegen (Admin)
DELETE /api/v1/users/{id}              → Benutzer deaktivieren (Admin)

# Projekte
GET    /api/v1/projects                → Eigene Projekte
POST   /api/v1/projects                → Neues Projekt
GET    /api/v1/projects/{id}           → Projektdetails
PUT    /api/v1/projects/{id}           → Projekt bearbeiten
DELETE /api/v1/projects/{id}           → Projekt archivieren
POST   /api/v1/projects/{id}/members   → Mitglied hinzufügen
DELETE /api/v1/projects/{id}/members/{uid} → Mitglied entfernen

# Scope
GET    /api/v1/projects/{id}/scope     → Scope-Ziele auflisten
POST   /api/v1/projects/{id}/scope     → Ziel hinzufügen
DELETE /api/v1/projects/{id}/scope/{tid} → Ziel entfernen
POST   /api/v1/projects/{id}/scope/validate → Scope validieren

# Scans
GET    /api/v1/projects/{id}/scans     → Alle Scans eines Projekts
POST   /api/v1/projects/{id}/scans     → Neuen Scan starten
GET    /api/v1/scans/{id}              → Scan-Details + Status
PUT    /api/v1/scans/{id}/pause        → Scan pausieren
PUT    /api/v1/scans/{id}/resume       → Scan fortsetzen
PUT    /api/v1/scans/{id}/cancel       → Scan abbrechen
GET    /api/v1/scans/{id}/jobs         → Alle Jobs eines Scans
GET    /api/v1/scans/{id}/timeline     → Zeitlicher Ablauf

# Findings
GET    /api/v1/projects/{id}/findings  → Alle Findings (gefiltert)
GET    /api/v1/findings/{id}           → Finding-Details
PUT    /api/v1/findings/{id}           → Finding bearbeiten (Status, Zuweisung)
POST   /api/v1/findings/{id}/comments  → Kommentar hinzufügen
PUT    /api/v1/findings/{id}/verify    → Finding verifizieren
GET    /api/v1/projects/{id}/findings/stats → Statistiken

# Reports
GET    /api/v1/projects/{id}/reports   → Alle Reports
POST   /api/v1/projects/{id}/reports   → Report generieren
GET    /api/v1/reports/{id}            → Report-Details
GET    /api/v1/reports/{id}/download   → Report herunterladen

# Scan-Historie & Vergleich
GET    /api/v1/projects/{id}/history   → Scan-Verlauf
POST   /api/v1/projects/{id}/compare   → Zwei Scans vergleichen

# Tools & Profile
GET    /api/v1/tools                   → Verfügbare Tools + Status
GET    /api/v1/profiles                → Scan-Profile
POST   /api/v1/profiles                → Custom-Profil erstellen

# Audit-Log
GET    /api/v1/audit-log               → Audit-Einträge (Admin)

# WebSocket
WS     /api/v1/ws/{project_id}         → Live-Updates (Scan-Status, Findings)
```

### 9.2 WebSocket-Events

```typescript
// Frontend → Backend
interface WSMessage {
  type: "subscribe" | "unsubscribe";
  scan_id?: string;
}

// Backend → Frontend
interface WSEvent {
  event: string;          // z.B. "scan.started", "tool.completed"
  scan_id: string;
  timestamp: string;      // ISO 8601
  data: Record<string, any>;
}

// Event-Typen:
// scan.started       → { profile, targets }
// scan.completed     → { total_findings }
// scan.failed        → { error }
// phase.started      → { phase, order }
// phase.completed    → { phase }
// tool.started       → { tool, target, phase }
// tool.completed     → { tool, target, findings_count, duration }
// tool.failed        → { tool, target, error }
// finding.created    → { id, title, severity, tool }
// finding.updated    → { id, status, updated_by }
```

---

## 10. Frontend-Architektur

### 10.1 Seitenstruktur

```
┌──────────────────────────────────────────────────────┐
│  Header (Logo, User-Menu, Benachrichtigungen)        │
├──────────┬───────────────────────────────────────────┤
│          │                                           │
│ Sidebar  │           Hauptbereich                    │
│          │                                           │
│ • Dash-  │  ┌─────────────────────────────────────┐  │
│   board  │  │                                     │  │
│ • Projek-│  │  Dynamischer Content                │  │
│   te     │  │  (je nach Route)                    │  │
│ • Scans  │  │                                     │  │
│ • Find-  │  │  • Dashboard: KPIs + Charts         │  │
│   ings   │  │  • Projekte: Tabelle + Details      │  │
│ • Reports│  │  • Scan: Live-Timeline + Status      │  │
│ • Team   │  │  • Findings: Filterbarer Explorer    │  │
│ • Audit  │  │  • Reports: Builder + Preview        │  │
│ • Einst. │  │                                     │  │
│          │  └─────────────────────────────────────┘  │
│          │                                           │
│          │  ┌─────────────────────────────────────┐  │
│          │  │ Activity Feed (WebSocket-Updates)    │  │
│          │  └─────────────────────────────────────┘  │
└──────────┴───────────────────────────────────────────┘
```

### 10.2 Schlüssel-Ansichten

**Dashboard:** Übersicht über aktive Projekte, laufende Scans, Finding-Verteilung (Donut-Chart nach Severity), letzte Aktivitäten, offene Tasks.

**Scan-Konfiguration:** Profil-Auswahl (Quick/Standard/Deep/Custom), Tool-Checkboxen mit Optionen, Ziel-Eingabe mit Scope-Validierung, geschätzte Dauer.

**Scan-Live-View:** Phasen-Timeline (welche Phase läuft gerade), Tool-Status-Karten (running/completed/failed), Live-Finding-Feed, Fortschrittsbalken.

**Finding-Explorer:** Tabelle mit Filter (Severity, Tool, Status, Host), Detail-Ansicht mit Evidence, Kommentar-Thread, Status-Workflow (Open → Confirmed → Remediated).

**Netzwerk-Topologie:** React Flow Visualisierung der gescannten Infrastruktur – Hosts als Nodes, Verbindungen als Edges, Farben nach Schwachstellen-Severity.

---

## 11. Authentifizierung & Autorisierung

### 11.1 JWT-basierte Authentifizierung

```python
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)
```

### 11.2 Rollen-basierte Zugriffskontrolle (RBAC)

| Berechtigung | Admin | Lead | Pentester | Viewer |
|-------------|-------|------|-----------|--------|
| Benutzer verwalten | ✅ | ❌ | ❌ | ❌ |
| Projekte erstellen | ✅ | ✅ | ❌ | ❌ |
| Team-Mitglieder zuweisen | ✅ | ✅ | ❌ | ❌ |
| Scope definieren | ✅ | ✅ | ✅ | ❌ |
| Scans starten/stoppen | ✅ | ✅ | ✅ | ❌ |
| Findings bearbeiten | ✅ | ✅ | ✅ | ❌ |
| Findings ansehen | ✅ | ✅ | ✅ | ✅ |
| Reports generieren | ✅ | ✅ | ✅ | ❌ |
| Reports ansehen | ✅ | ✅ | ✅ | ✅ |
| Audit-Log einsehen | ✅ | ✅ | ❌ | ❌ |
| System-Einstellungen | ✅ | ❌ | ❌ | ❌ |

---

## 12. Sicherheit & DSGVO

### 12.1 Datensicherheit

- **Verschlüsselung at rest:** Sensible Felder (Passwort-Hashes, API-Keys) in der Datenbank. PostgreSQL Transparent Data Encryption (TDE) oder Application-Level-Verschlüsselung mit Fernet.
- **Verschlüsselung in transit:** Alle Kommunikation über TLS 1.3 (Nginx terminiert TLS).
- **Secret Management:** Umgebungsvariablen für Secrets (`.env` Datei, gitignored). Für Produktion: HashiCorp Vault oder SOPS.
- **Passwort-Policy:** Mindestens 12 Zeichen, bcrypt mit Cost Factor 12.

### 12.2 DSGVO-Konformität

- **Datentrennung:** Strikte Isolation zwischen Kundenprojekten über `project_id` Foreign Keys und API-Level-Filterung.
- **Automatische Löschung:** `auto_delete_at` Feld auf Projekten. Cronjob prüft täglich und löscht abgelaufene Projekte inkl. aller zugehörigen Daten (CASCADE).
- **Datenexport:** API-Endpunkt für vollständigen Datenexport eines Projekts als JSON.
- **Audit-Trail:** Lückenlose Protokollierung aller Zugriffe und Änderungen.
- **Zugriffsminimierung:** Pentester sehen nur Projekte, denen sie zugewiesen sind.

### 12.3 Scope-Validierung

```python
import ipaddress
import re
from dataclasses import dataclass


@dataclass
class ScopeValidationResult:
    is_valid: bool
    reason: str = ""


class ScopeValidator:
    """
    Validiert ob ein Scan-Ziel im autorisierten Scope liegt.
    Wird VOR jedem Tool-Aufruf geprüft.
    """

    def __init__(self, allowed_targets: list[dict], excluded_targets: list[dict] | None = None):
        self.allowed = allowed_targets      # [{"type": "domain", "value": "example.com"}, ...]
        self.excluded = excluded_targets or []

    def validate(self, target: str) -> ScopeValidationResult:
        """Prüft ob ein Ziel im Scope liegt."""

        # Zuerst Ausschlüsse prüfen
        for excl in self.excluded:
            if self._matches(target, excl):
                return ScopeValidationResult(
                    is_valid=False,
                    reason=f"Target '{target}' is explicitly excluded from scope"
                )

        # Dann Erlaubnis prüfen
        for allowed in self.allowed:
            if self._matches(target, allowed):
                return ScopeValidationResult(is_valid=True)

        return ScopeValidationResult(
            is_valid=False,
            reason=f"Target '{target}' is not in the authorized scope"
        )

    def _matches(self, target: str, scope_entry: dict) -> bool:
        """Prüft ob ein Ziel zu einem Scope-Eintrag passt."""
        scope_type = scope_entry["type"]
        scope_value = scope_entry["value"]

        if scope_type == "domain":
            return target == scope_value or target.endswith(f".{scope_value}")

        elif scope_type == "ip":
            return target == scope_value

        elif scope_type == "ip_range":
            try:
                network = ipaddress.ip_network(scope_value, strict=False)
                ip = ipaddress.ip_address(target)
                return ip in network
            except ValueError:
                return False

        elif scope_type == "url":
            return target.startswith(scope_value)

        return False
```

---

## 13. Reporting-Engine

### 13.1 Report-Struktur

```
Executive Summary
├── Projekt-Übersicht (Kunde, Zeitraum, Scope)
├── Risiko-Zusammenfassung (Donut-Chart)
├── Top-5 kritische Findings
└── Empfehlungen (priorisiert)

Technischer Bericht
├── Methodik
├── Scope & Ziele
├── Finding-Übersicht (Tabelle nach Severity)
├── Detaillierte Findings
│   ├── Titel & Severity
│   ├── Betroffene Systeme
│   ├── Beschreibung & Impact
│   ├── Reproduktionsschritte / Evidence
│   ├── Empfehlung / Remediation
│   └── CVSS Score & Referenzen
├── Netzwerk-Topologie
└── Anhang (Tool-Outputs, Scan-Konfiguration)
```

### 13.2 Report-Generierung (WeasyPrint)

```python
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import weasyprint


class ReportGenerator:
    """Generates PDF/HTML reports from scan findings."""

    def __init__(self, template_dir: str = "app/reporting/templates"):
        self.env = Environment(loader=FileSystemLoader(template_dir))

    async def generate_pdf(
        self,
        project: dict,
        findings: list[dict],
        config: dict,
    ) -> Path:
        """
        Generate a PDF report.

        Args:
            project: Project metadata (name, client, dates)
            findings: List of findings sorted by severity
            config: Report config (template, logo_path, colors, etc.)

        Returns:
            Path to the generated PDF file
        """
        template = self.env.get_template(
            config.get("template", "technical_report.html")
        )

        severity_counts = {
            "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0
        }
        for f in findings:
            severity_counts[f["severity"]] = severity_counts.get(f["severity"], 0) + 1

        html_content = template.render(
            project=project,
            findings=findings,
            severity_counts=severity_counts,
            generated_at=datetime.now(timezone.utc).isoformat(),
            logo_path=config.get("logo_path"),
            primary_color=config.get("primary_color", "#1a1a2e"),
        )

        output_path = Path(f"data/reports/{project['id']}/{datetime.now():%Y%m%d_%H%M%S}.pdf")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        weasyprint.HTML(string=html_content).write_pdf(str(output_path))

        return output_path
```

---

## 14. Deployment & Infrastruktur

### 14.1 Docker Compose (Produktion)

```yaml
version: "3.9"

services:
  # === Reverse Proxy ===
  nginx:
    image: nginx:1.25-alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - frontend_build:/usr/share/nginx/html:ro
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

  # === Backend API ===
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql+asyncpg://reconforge:${DB_PASSWORD}@postgres:5432/reconforge
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    volumes:
      - scan_data:/app/data        # Scan-Artefakte & Reports
      - tool_configs:/app/configs  # Tool-Konfigurationen
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  # === Celery Worker ===
  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A workers.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=postgresql+asyncpg://reconforge:${DB_PASSWORD}@postgres:5432/reconforge
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - scan_data:/app/data
      - tool_configs:/app/configs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    # Sicherheitstools brauchen teilweise Root oder NET_RAW
    cap_add:
      - NET_RAW
      - NET_ADMIN

  # === Celery Beat (Scheduler) ===
  beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A workers.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://reconforge:${DB_PASSWORD}@postgres:5432/reconforge
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    restart: unless-stopped

  # === Frontend (Build) ===
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    volumes:
      - frontend_build:/app/dist

  # === Datenbank ===
  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=reconforge
      - POSTGRES_USER=reconforge
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U reconforge"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # === Redis ===
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  scan_data:
  tool_configs:
  frontend_build:
```

### 14.2 Backend Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# System-Dependencies für Sicherheitstools
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    nikto \
    hydra \
    curl \
    wget \
    git \
    ruby \
    ruby-dev \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Go-basierte Tools installieren (subfinder, httpx, nuclei, ffuf, dnsx)
RUN curl -sL https://go.dev/dl/go1.22.0.linux-amd64.tar.gz | tar xz -C /usr/local
ENV PATH="/usr/local/go/bin:/root/go/bin:${PATH}"

RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest \
    && go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest \
    && go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest \
    && go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest \
    && go install -v github.com/ffuf/ffuf/v2@latest

# Nuclei-Templates herunterladen
RUN nuclei -update-templates

# WPScan installieren
RUN gem install wpscan

# Python-Dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[prod]"

# App-Code kopieren
COPY . .

# Non-root User für API (Worker braucht ggf. Root für nmap)
RUN useradd -m appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 14.3 Umgebungsvariablen (.env.example)

```bash
# === Datenbank ===
DB_PASSWORD=changeme_strong_password_here
DATABASE_URL=postgresql+asyncpg://reconforge:${DB_PASSWORD}@postgres:5432/reconforge

# === Redis ===
REDIS_PASSWORD=changeme_redis_password
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

# === Sicherheit ===
SECRET_KEY=changeme_generate_with_openssl_rand_hex_32
ENVIRONMENT=production

# === API ===
API_V1_PREFIX=/api/v1
BACKEND_CORS_ORIGINS=["https://reconforge.local"]

# === Tool-API-Keys (optional) ===
WPSCAN_API_TOKEN=
SHODAN_API_KEY=
CENSYS_API_ID=
CENSYS_API_SECRET=
VIRUSTOTAL_API_KEY=
```

---

## 15. Epics & Roadmap

### 15.1 Implementierungsreihenfolge

```
Phase 1: Fundament (Wochen 1–3)
├── Epic 1: Projekt-Setup & Grundstruktur
│   ├── Monorepo aufsetzen
│   ├── Docker Compose Konfiguration
│   ├── FastAPI Grundgerüst + Health-Check
│   ├── React App Grundgerüst
│   ├── PostgreSQL + Alembic Migrationen
│   └── CI/CD Pipeline (optional)
│
├── Epic 2: Auth & Team-Management
│   ├── User-Model + CRUD
│   ├── JWT Login/Logout/Refresh
│   ├── RBAC Middleware
│   ├── Projekt-CRUD + Mitgliederverwaltung
│   └── Audit-Log Middleware

Phase 2: Kern-Funktionalität (Wochen 4–8)
├── Epic 3: Scope-Management
│   ├── Scope-Target CRUD
│   ├── Scope-Validierung (vor jedem Scan)
│   ├── Dokumenten-Upload (Genehmigungen)
│   └── Scope-Übersicht im Frontend
│
├── Epic 4: Tool-Integration Layer (Welle 1)
│   ├── BaseToolWrapper + ToolResult
│   ├── ToolRegistry
│   ├── Nmap Wrapper
│   ├── Subfinder Wrapper
│   ├── httpx Wrapper
│   ├── Nuclei Wrapper
│   ├── Nikto Wrapper
│   ├── ffuf Wrapper
│   ├── SSLyze Wrapper
│   ├── SQLMap Wrapper
│   └── Integration-Tests für jeden Wrapper
│
├── Epic 5: Scan-Orchestrator
│   ├── Scan-Profile definieren
│   ├── Pipeline-Engine
│   ├── Celery Task-Integration
│   ├── Chain Logic Engine
│   ├── WebSocket Live-Updates
│   └── Scan Start/Stop/Pause API

Phase 3: Ergebnisse & UI (Wochen 9–13)
├── Epic 6: Ergebnis-Aggregation
│   ├── Finding-Normalisierung
│   ├── Fingerprint-basierte Deduplizierung
│   ├── CVSS-Scoring
│   ├── Finding-Workflow (Status-Management)
│   ├── Kommentar-System
│   └── Scan-Vergleich
│
├── Epic 7: Dashboard & UI
│   ├── Login-Seite
│   ├── Dashboard mit KPIs
│   ├── Projekt-Übersicht
│   ├── Scan-Konfiguration & Live-View
│   ├── Finding-Explorer mit Filtern
│   ├── Netzwerk-Topologie
│   ├── Team-Management UI
│   └── Activity Feed

Phase 4: Professionalisierung (Wochen 14–16)
├── Epic 8: Reporting
│   ├── HTML-Template für Executive Summary
│   ├── HTML-Template für technischen Bericht
│   ├── WeasyPrint PDF-Generierung
│   ├── JSON/CSV Export
│   ├── Report-Builder im Frontend
│   └── Kundenlogo + Branding

Phase 5: Erweiterung (fortlaufend)
├── Tool-Integration Welle 2
│   ├── theHarvester, WPScan, Hydra
│   ├── enum4linux-ng, BloodHound CE
│   ├── Arjun, LinkFinder, SecretFinder
│   └── Weitere Chain-Logic-Regeln
│
└── Tool-Integration Welle 3 (modular)
    ├── Prowler / ScoutSuite (Cloud)
    ├── NetExec / Kerbrute (AD)
    ├── Maigret / Sherlock (OSINT)
    └── Bettercap (Wireless)
```

### 15.2 Geschätzter Zeitrahmen

| Phase | Dauer | Beschreibung |
|-------|-------|-------------|
| Phase 1 | 3 Wochen | Fundament: Setup, Auth, DB |
| Phase 2 | 5 Wochen | Kern: Scope, Tools, Orchestrator |
| Phase 3 | 5 Wochen | UI + Ergebnis-Aggregation |
| Phase 4 | 2 Wochen | Reporting |
| Phase 5 | fortlaufend | Erweiterungen |
| **Gesamt bis MVP** | **~15 Wochen** | **Funktionsfähiges Tool mit Welle-1-Tools** |

---

## 16. Anhang: Tool-Referenz

### 16.1 Integrierte Tools (Gesamt)

| # | Tool | Kategorie | Welle | Integration | JSON-Output |
|---|------|-----------|-------|-------------|-------------|
| 1 | nmap | Discovery | Bestehend | subprocess (XML) | ✅ |
| 2 | recon-ng | OSINT | Bestehend | subprocess | ⚠️ |
| 3 | nikto | Web-Scanning | Bestehend | subprocess | ✅ |
| 4 | sqlmap | Exploitation | Bestehend | subprocess | ✅ |
| 5 | metasploit | Exploitation | Bestehend | RPC API | ✅ |
| 6 | **nuclei** | Vuln-Scanning | Welle 1 | subprocess (JSONL) | ✅ |
| 7 | **subfinder** | Subdomain-Enum | Welle 1 | subprocess (JSONL) | ✅ |
| 8 | **httpx** | Probing | Welle 1 | subprocess (JSONL) | ✅ |
| 9 | **ffuf** | Web-Fuzzing | Welle 1 | subprocess (JSON) | ✅ |
| 10 | **impacket** | Netzwerk/AD | Welle 1 | **Python import** | — |
| 11 | **sslyze** | SSL/TLS | Welle 1 | **Python import** | ✅ |
| 12 | theHarvester | OSINT | Welle 2 | Python import | ✅ |
| 13 | wpscan | CMS-Scanning | Welle 2 | subprocess (JSON) | ✅ |
| 14 | hydra | Auth-Testing | Welle 2 | subprocess (JSON) | ✅ |
| 15 | enum4linux-ng | SMB-Enum | Welle 2 | subprocess (JSON) | ✅ |
| 16 | BloodHound CE | AD-Analyse | Welle 2 | REST API | ✅ |
| 17 | arjun | API-Params | Welle 2 | Python import | ✅ |
| 18 | LinkFinder | JS-Analyse | Welle 2 | Python import | ⚠️ |
| 19 | SecretFinder | JS-Secrets | Welle 2 | Python import | ⚠️ |

### 16.2 Modulare Erweiterungen (Welle 3)

| Tool | Einsatz-Szenario |
|------|-----------------|
| Prowler | Cloud-Kunden (AWS/Azure/GCP) |
| ScoutSuite | Cloud-Konfigurations-Audit |
| NetExec | Windows-Netzwerke |
| Kerbrute | Active Directory |
| Maigret | Social-Engineering-Scope |
| Sherlock | Social-Media-Recon |
| dnstwist | Phishing-Analyse |
| Bettercap | Wireless-Pentesting |
| Trivy | Container-Umgebungen |
| ExifTool | Dokumenten-OSINT |

---

## Glossar

| Begriff | Bedeutung |
|---------|-----------|
| **Chain Logic** | Automatische Auslösung von Folge-Scans basierend auf Ergebnissen |
| **Finding** | Eine einzelne Schwachstelle oder sicherheitsrelevante Information |
| **Fingerprint** | SHA-256 Hash zur Erkennung doppelter Findings |
| **Phase** | Ein Abschnitt im Scan-Ablauf (z.B. OSINT, Discovery, Scanning) |
| **Scope** | Die autorisierten Ziele eines Pentests |
| **Wrapper** | Python-Klasse die ein externes Tool kapselt und normalisiert |
| **Worker** | Celery-Prozess der Scan-Jobs asynchron ausführt |

---

> **Nächster Schritt:** Epic 1 – Projekt-Setup & Grundstruktur implementieren.
