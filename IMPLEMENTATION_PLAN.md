# ReconForge — Implementation Plan

> **Version:** 1.0 | **Datum:** 24. Februar 2026  
> **Ziel:** 10 Features parallel umsetzbar (Python-Dev + React-Dev)

---

## Übersicht & Abhängigkeiten

```
P1 (Scan Dispatch) ──→ P2 (Auto-Discover) ──→ P3 (Output Parsing)
       │                                              │
       │         P6 (Structured Logging) ←────────────┤
       │                                              │
       ▼                                              ▼
P9 (WebSocket Progress) ──→ P10 (Notifications) ──→ P8 (Reporting/PDF)
       
P4 (Smoke Tests) ←── P5 (Health Endpoint)
P7 (DB Backup) — standalone
```

**Kritischer Pfad:** P1 → P2 → P3 → P8  
**Parallel-Track DevOps:** P4, P5, P6, P7 (unabhängig, sofort startbar)  
**Parallel-Track Frontend:** P9, P10 (nach P1 Backend-Events)

---

## Sprint-Planung

| Sprint | Python-Dev | React-Dev | DevOps |
|--------|-----------|-----------|--------|
| **1** (3d) | P1: Scan Dispatch | P9: WebSocket UI | P6: Structured Logging |
| **2** (3d) | P2: Auto-Discover | P10: Notifications | P5: Health Endpoint + P4: Smoke Tests |
| **3** (2d) | P3: Output Parsing | P8: Report UI | P7: DB Backup |
| **4** (2d) | P8: Report Backend | P8: Report UI polish | Integration Tests |

---

## P1: Scan Dispatch — Tools tatsächlich ausführen

**Status:** Celery Task existiert, PipelineEngine existiert, BaseToolWrapper.run() hat subprocess-Logik.  
**Problem:** Die Tool-Wrapper haben `build_command()` und `parse_output()`, aber es ist unklar ob alle korrekt implementiert sind. Der Celery-Task ruft `PipelineEngine.execute_scan()` auf — das ist bereits verdrahtet.

### Dateien

| Datei | Änderung |
|-------|----------|
| `backend/workers/tasks/scan_tasks.py` | Error handling verbessern, Retry-Logic, Status-Updates bei Failure |
| `backend/app/orchestrator/engine.py` | Raw-Output auf Filesystem speichern (`raw_output_path`), Timeout pro Tool konfigurierbar |
| `backend/app/tools/base.py` | `run()`: Output-Datei schreiben nach `/data/scans/{scan_id}/{tool}_{target}_{timestamp}.raw` |
| `backend/app/api/v1/scans.py` | Celery Task Dispatch beim POST `/scans/` — verify `.delay()` wird aufgerufen |
| `backend/app/tools/scanning/nmap.py` | Verify `build_command()` + `parse_output()` funktionieren |
| `backend/app/tools/scanning/nuclei.py` | Verify JSONL parsing |
| `backend/app/tools/recon/subfinder.py` | Verify JSONL output parsing |
| `backend/app/tools/recon/httpx.py` | Verify JSONL output parsing |

### Implementierung

1. **Verify Tool Wrappers** — Jeden Wrapper manuell testen: `build_command()` aufrufen, Output prüfen
2. **Raw Output Persistence** — In `BaseToolWrapper.run()` nach erfolgreichem Lauf den Output speichern:
   ```python
   # In base.py run(), nach parse_output():
   output_dir = Path(f"/data/scans/{scan_id}")
   output_dir.mkdir(parents=True, exist_ok=True)
   output_path = output_dir / f"{self.name}_{target}_{int(time.time())}.raw"
   output_path.write_text(raw_output)
   result.raw_output_path = str(output_path)
   ```
3. **Celery Retry** — `@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)`
4. **Scan Status Updates** — Bei Task-Start `scan.status = "running"` (existiert bereits), bei Exception → `"failed"` mit `error_message`
5. **Integration Test** — `test_scan_dispatch.py`: Mock-subprocess, verify ScanJob + Finding Einträge

### Abhängigkeiten
- Keine Vorbedingungen
- **Voraussetzung für:** P2, P3, P9

### Akzeptanzkriterien
- [ ] `POST /api/v1/scans/` dispatcht Celery Task
- [ ] Celery Worker führt Nmap tatsächlich via `subprocess` aus
- [ ] ScanJob-Einträge haben `status=completed` und `raw_output_path` gesetzt
- [ ] Findings werden aus Tool-Output in DB geschrieben
- [ ] Bei Tool-Fehler: ScanJob `status=failed`, `error_message` gesetzt
- [ ] WebSocket Events `scan.started`, `tool.started`, `tool.completed`, `scan.completed` werden gesendet

---

## P2: Auto-Discover Backend

**Status:** Frontend hat Auto-Discover Toggles (`subdomains`, `technologies`, `ports`). Backend-Logik fehlt.

### Dateien

| Datei | Änderung |
|-------|----------|
| `backend/app/orchestrator/engine.py` | Neue Methode `_build_auto_discover_phases()` |
| `backend/app/orchestrator/profiles.py` | Neues Profil `"auto_discover"` oder dynamischer Profile-Builder |
| `backend/app/api/v1/scans.py` | `auto_discover` Config aus Request Body extrahieren, in Profile umwandeln |
| `backend/app/schemas/scan.py` | `AutoDiscoverConfig` Schema: `subdomains: bool, technologies: bool, ports: bool` |

### Implementierung

1. **Schema definieren:**
   ```python
   class AutoDiscoverConfig(BaseModel):
       subdomains: bool = False
       technologies: bool = False
       ports: bool = False
   ```

2. **Dynamischen Profile-Builder:**
   ```python
   def build_auto_discover_profile(config: AutoDiscoverConfig) -> ScanProfile:
       phases = []
       order = 1
       
       if config.subdomains:
           phases.append(ScanPhase(
               name="Subdomain Discovery",
               order=order,
               tools=[ToolConfig("subfinder"), ToolConfig("amass")],
           ))
           order += 1
           # Automatisch httpx nachschalten für live-check
           phases.append(ScanPhase(
               name="HTTP Probing",
               order=order,
               tools=[ToolConfig("httpx", config={"tech_detect": True})],
           ))
           order += 1
       
       if config.ports:
           phases.append(ScanPhase(
               name="Port Scanning",
               order=order,
               tools=[ToolConfig("nmap", config={"scan_type": "full"})],
           ))
           order += 1
       
       if config.technologies:
           phases.append(ScanPhase(
               name="Technology Detection",
               order=order,
               tools=[ToolConfig("whatweb"), ToolConfig("httpx", config={"tech_detect": True})],
           ))
           order += 1
       
       return ScanProfile(
           name="Auto-Discover",
           description="Dynamic profile based on auto-discover settings",
           phases=phases,
       )
   ```

3. **API Integration** — In `POST /scans/`: Wenn `auto_discover` im Request → `build_auto_discover_profile()` statt festes Profil

### Abhängigkeiten
- **Benötigt:** P1 (Scan Dispatch muss funktionieren)
- **Voraussetzung für:** Nichts direkt

### Akzeptanzkriterien
- [ ] `POST /scans/` mit `{"auto_discover": {"subdomains": true}}` → Subfinder + Amass werden ausgeführt
- [ ] `technologies: true` → WhatWeb wird ausgeführt
- [ ] `ports: true` → Nmap full port scan (`-p-`)
- [ ] Kombinationen funktionieren (alle drei gleichzeitig)
- [ ] Chain Logic greift: Subfinder-Ergebnisse → httpx → ggf. Nuclei

---

## P3: Tool Output Parsing

**Status:** Parser-Stubs existieren in den Wrappern (`parse_output()`). Müssen validiert/vervollständigt werden.

### Dateien

| Datei | Änderung |
|-------|----------|
| `backend/app/tools/scanning/nmap.py` | XML-Parser validieren, Edge-Cases (kein Host, geschlossene Ports) |
| `backend/app/tools/scanning/nuclei.py` | JSONL-Parser validieren, CVSS-Score extrahieren |
| `backend/app/tools/recon/subfinder.py` | JSON-Output → Hosts-Liste |
| `backend/app/tools/recon/httpx.py` | JSONL → URLs + Tech-Stack + Status-Codes |
| `backend/app/tools/web_analysis/whatweb.py` | JSON-Output → Technology Findings |
| `backend/app/tools/scanning/nikto.py` | CSV/JSON-Output → Vulnerability Findings |
| `backend/app/tools/scanning/ffuf.py` | JSON-Output → Directory/File Findings |
| `backend/app/tools/web_analysis/sslyze.py` | Python-API Output (existiert bereits) |
| `backend/app/tools/web_analysis/testssl.py` | JSON-Output → SSL Findings |
| `backend/app/services/finding_service.py` | `normalize_severity()` — einheitliches Severity-Mapping |
| `backend/tests/test_tools/` | Fixture-Dateien mit echtem Tool-Output für jeden Parser |

### Implementierung

1. **Test-Fixtures sammeln** — Für jedes Tool echten Output als Datei speichern:
   ```
   backend/tests/fixtures/
   ├── nmap_service_scan.xml
   ├── nuclei_scan.jsonl
   ├── subfinder_output.json
   ├── httpx_output.jsonl
   ├── whatweb_output.json
   └── nikto_output.json
   ```

2. **Parser-Tests schreiben** — Für jeden Wrapper:
   ```python
   def test_nmap_parse_output():
       raw = Path("tests/fixtures/nmap_service_scan.xml").read_text()
       wrapper = NmapWrapper()
       result = wrapper.parse_output(raw, "10.0.0.1")
       assert result.status == ToolStatus.COMPLETED
       assert len(result.hosts) >= 1
       assert any(f["severity"] == "info" for f in result.findings)
   ```

3. **Severity Normalisierung** — Einheitliches Mapping in `finding_service.py`:
   ```python
   SEVERITY_MAP = {
       "critical": "critical", "high": "high", "medium": "medium",
       "low": "low", "info": "info", "informational": "info",
       "none": "info", "unknown": "info",
   }
   ```

4. **Edge Cases** — Leerer Output, malformed XML/JSON, Timeout-Output

### Abhängigkeiten
- **Benötigt:** P1 (damit Output tatsächlich generiert wird)
- **Voraussetzung für:** P8 (Reporting braucht saubere Findings)

### Akzeptanzkriterien
- [ ] Jeder Tool-Wrapper hat mindestens 1 Test mit echtem Fixture-Output
- [ ] Nmap XML → `hosts[]` mit Ports, Services, OS; `findings[]` mit offenen Ports
- [ ] Nuclei JSONL → Findings mit Severity, CVE, CWE, Description
- [ ] Subfinder → `hosts[]` mit Subdomains
- [ ] Alle Parser graceful bei leerem/malformed Output (kein Crash, `status=FAILED`)
- [ ] Findings in DB haben korrekte `severity`, `source_tool`, `fingerprint`

---

## P4: Post-Deploy Smoke Tests

**Status:** `.github/workflows/deploy.yml` existiert, kein Post-Deploy-Check.

### Dateien

| Datei | Änderung |
|-------|----------|
| `.github/workflows/deploy.yml` | Neuer Step nach Deploy: Smoke Tests |
| `scripts/smoke_test.sh` | Neues Script: Health + Login + API-Check |

### Implementierung

```yaml
# In deploy.yml, nach dem Deploy-Step:
- name: Post-Deploy Smoke Tests
  run: |
    sleep 15  # Warten bis Pod ready
    
    # Health Check
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://reconforge.example.com/health)
    if [ "$HTTP_CODE" != "200" ]; then
      echo "Health check failed: HTTP $HTTP_CODE"
      exit 1
    fi
    
    # Login Check
    TOKEN=$(curl -s -X POST https://reconforge.example.com/api/v1/auth/login \
      -H "Content-Type: application/json" \
      -d '{"email":"smoke@test.local","password":"${{ secrets.SMOKE_TEST_PASSWORD }}"}' \
      | jq -r '.access_token')
    
    if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
      echo "Login check failed"
      exit 1
    fi
    
    # API Check (list projects)
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
      -H "Authorization: Bearer $TOKEN" \
      https://reconforge.example.com/api/v1/projects/)
    
    if [ "$HTTP_CODE" != "200" ]; then
      echo "API check failed: HTTP $HTTP_CODE"
      exit 1
    fi
    
    echo "All smoke tests passed"
```

### Abhängigkeiten
- **Benötigt:** P5 (Health Endpoint muss robust sein)
- **Voraussetzung für:** Nichts

### Akzeptanzkriterien
- [ ] CI Pipeline bricht ab wenn Health-Endpoint nach Deploy nicht erreichbar
- [ ] CI Pipeline bricht ab wenn Login fehlschlägt
- [ ] CI Pipeline bricht ab wenn API-Endpunkt 4xx/5xx zurückgibt
- [ ] Smoke-Test-User existiert in Seed-Daten

---

## P5: Health/Status Endpoint verbessern

**Status:** `/health` existiert, liefert vermutlich nur `{"status": "ok"}`.

### Dateien

| Datei | Änderung |
|-------|----------|
| `backend/app/main.py` | `/health` erweitern mit DB + Redis + Celery Check |
| `backend/app/api/v1/router.py` | Optionaler `/api/v1/status` Endpoint (authentifiziert, detailliert) |

### Implementierung

```python
@app.get("/health")
async def health_check():
    """Unauthenticated, für k8s probes + CI."""
    checks = {"api": "ok"}
    
    # DB Check
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
    
    # Redis Check
    try:
        redis = get_redis()
        await redis.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"
    
    healthy = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "healthy" if healthy else "degraded", "checks": checks},
    )

@router.get("/status")
async def detailed_status(current_user = Depends(get_current_admin_user)):
    """Authentifiziert, für Monitoring-Dashboard."""
    # ... DB, Redis, Celery Worker Count, aktive Scans, Queue-Länge
```

### Abhängigkeiten
- Keine
- **Voraussetzung für:** P4 (Smoke Tests)

### Akzeptanzkriterien
- [ ] `/health` prüft DB + Redis Connectivity
- [ ] Returns HTTP 503 wenn DB oder Redis down
- [ ] `/api/v1/status` (auth required) zeigt Celery Worker Count + Queue Length
- [ ] k3s liveness/readiness Probes nutzen `/health`

---

## P6: Structured Logging

**Status:** Aktuell `logging.getLogger(__name__)` überall, aber kein einheitliches Format.

### Dateien

| Datei | Änderung |
|-------|----------|
| `backend/app/core/logging.py` | **Neu:** Logging-Konfiguration mit structlog |
| `backend/app/main.py` | Logging-Setup beim App-Start |
| `backend/app/tools/base.py` | Structured log fields: `tool`, `target`, `duration`, `status` |
| `backend/app/orchestrator/engine.py` | Structured log fields: `scan_id`, `phase`, `tool` |
| `backend/workers/celery_app.py` | Celery Worker Logging konfigurieren |
| `backend/pyproject.toml` | `structlog` als Dependency |

### Implementierung

```python
# backend/app/core/logging.py
import structlog
import logging
import sys

def setup_logging(log_level: str = "INFO", json_output: bool = True):
    """Configure structured logging for the application."""
    
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
    
    # Bridge stdlib logging to structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level),
    )
```

Usage in tools:
```python
log = structlog.get_logger()
log.info("tool.execution.start", tool=self.name, target=target, config=config)
# ... nach Ausführung:
log.info("tool.execution.complete", tool=self.name, target=target, 
         duration=duration, findings_count=len(result.findings), status=result.status.value)
```

### Abhängigkeiten
- Keine
- **Empfohlen vor:** P1 (damit Scan-Execution gut geloggt wird)

### Akzeptanzkriterien
- [ ] Alle Logs im JSON-Format (Production) oder colored Console (Development)
- [ ] Scan-Execution Logs enthalten: `scan_id`, `tool`, `target`, `duration`, `status`
- [ ] Errors enthalten Stack-Traces
- [ ] Celery Worker Logs im gleichen Format
- [ ] Log-Level konfigurierbar via `LOG_LEVEL` Env-Variable

---

## P7: DB Backup Cron

**Status:** `scripts/backup.sh` existiert, kein Cron-Setup.

### Dateien

| Datei | Änderung |
|-------|----------|
| `scripts/backup.sh` | Validieren/verbessern: Compression, Retention, Error Handling |
| `docker-compose.yml` | Backup-Service oder Cron im Backend-Container |
| `k3s.yaml` | CronJob Manifest für k3s |

### Implementierung

```yaml
# k3s.yaml — CronJob
apiVersion: batch/v1
kind: CronJob
metadata:
  name: reconforge-db-backup
  namespace: flow
spec:
  schedule: "0 2 * * *"  # Täglich 02:00 UTC
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:16-alpine
            command:
            - /bin/sh
            - -c
            - |
              TIMESTAMP=$(date +%Y%m%d_%H%M%S)
              BACKUP_FILE="/backups/reconforge_${TIMESTAMP}.sql.gz"
              pg_dump $DATABASE_URL | gzip > $BACKUP_FILE
              # Retention: Keep last 14 days
              find /backups -name "reconforge_*.sql.gz" -mtime +14 -delete
              echo "Backup completed: $BACKUP_FILE"
            envFrom:
            - secretRef:
                name: reconforge-secrets
            volumeMounts:
            - name: backup-volume
              mountPath: /backups
          restartPolicy: OnFailure
          volumes:
          - name: backup-volume
            persistentVolumeClaim:
              claimName: reconforge-backups
```

### Abhängigkeiten
- Keine

### Akzeptanzkriterien
- [ ] Backup läuft täglich um 02:00 UTC automatisch
- [ ] Backup ist komprimiert (gzip)
- [ ] Retention: 14 Tage, ältere werden gelöscht
- [ ] Backup-Fehler werden geloggt
- [ ] Restore getestet und dokumentiert: `gunzip -c backup.sql.gz | psql $DATABASE_URL`

---

## P8: Reporting Engine — PDF mit WeasyPrint

**Status:** `backend/app/reporting/` Verzeichnis existiert (leer oder Stubs). WeasyPrint im Tech-Stack vorgesehen.

### Dateien — Backend

| Datei | Änderung |
|-------|----------|
| `backend/app/reporting/generator.py` | Report-Generierung: Findings laden, HTML rendern, PDF erstellen |
| `backend/app/reporting/templates/executive_summary.html` | Jinja2 HTML Template |
| `backend/app/reporting/templates/technical_report.html` | Detailliertes Template |
| `backend/app/reporting/templates/styles.css` | Print-optimiertes CSS |
| `backend/app/reporting/exporters/pdf.py` | WeasyPrint HTML→PDF |
| `backend/app/api/v1/reports.py` | `POST /reports/generate`, `GET /reports/{id}/download` |
| `backend/workers/tasks/report_tasks.py` | Celery Task für Report-Generierung (async) |
| `backend/pyproject.toml` | `weasyprint`, `jinja2` Dependencies |

### Dateien — Frontend

| Datei | Änderung |
|-------|----------|
| `frontend/src/pages/Reports.tsx` | Report-Builder UI: Scan wählen, Template wählen, Severity-Filter |
| `frontend/src/components/reports/ReportBuilder.tsx` | Konfigurationsformular |
| `frontend/src/components/reports/ReportPreview.tsx` | HTML-Vorschau vor PDF-Export |
| `frontend/src/api/reports.ts` | API Client: generate, download, list |

### Implementierung — Backend

```python
# backend/app/reporting/generator.py
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

TEMPLATE_DIR = Path(__file__).parent / "templates"

class ReportGenerator:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    
    async def generate_pdf(
        self,
        project: dict,
        findings: list[dict],
        scan: dict,
        template_name: str = "technical_report.html",
        config: dict | None = None,
    ) -> bytes:
        template = self.env.get_template(template_name)
        
        # Group findings by severity
        by_severity = {"critical": [], "high": [], "medium": [], "low": [], "info": []}
        for f in findings:
            by_severity.get(f["severity"], by_severity["info"]).append(f)
        
        html_content = template.render(
            project=project,
            scan=scan,
            findings=findings,
            by_severity=by_severity,
            stats={
                "total": len(findings),
                "critical": len(by_severity["critical"]),
                "high": len(by_severity["high"]),
                "medium": len(by_severity["medium"]),
                "low": len(by_severity["low"]),
                "info": len(by_severity["info"]),
            },
            config=config or {},
        )
        
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
```

### Implementierung — Frontend (React-Dev)

- **ReportBuilder:** Dropdown Scan wählen, Checkboxen für Severity-Filter, Template-Auswahl
- **Generate Button** → `POST /api/v1/reports/generate` → zeigt Progress → Download-Link
- **Report-Liste** → `GET /api/v1/reports/` → Tabelle mit Download-Buttons

### Abhängigkeiten
- **Benötigt:** P3 (Findings müssen korrekt geparst sein)
- **Voraussetzung für:** Nichts

### Akzeptanzkriterien
- [ ] `POST /api/v1/reports/generate` erstellt PDF asynchron (Celery Task)
- [ ] PDF enthält: Executive Summary, Findings nach Severity sortiert, Evidence
- [ ] PDF hat professionelles Layout (Logo-Platzhalter, Seitenzahlen, Inhaltsverzeichnis)
- [ ] `GET /api/v1/reports/{id}/download` liefert PDF-Datei
- [ ] Frontend: Report-Builder UI funktional
- [ ] Mindestens 2 Templates: Executive Summary (1-2 Seiten) + Technical Report (detailliert)

---

## P9: Real-time Scan Progress via WebSocket

**Status:** `ws_router` existiert in `backend/app/api/v1/websocket.py`. `WebSocketEventManager` sendet Events. Frontend `useWebSocket` Hook existiert.

### Dateien — Backend

| Datei | Änderung |
|-------|----------|
| `backend/app/core/events.py` | Scan-spezifische Subscriptions (per `scan_id`), Progress-Berechnung |
| `backend/app/orchestrator/engine.py` | Mehr granulare Events: `tool.progress` (0-100%), Phase-Progress |

### Dateien — Frontend

| Datei | Änderung |
|-------|----------|
| `frontend/src/hooks/useWebSocket.ts` | Reconnection-Logic, Event-Parsing verbessern |
| `frontend/src/components/scans/ScanProgress.tsx` | Live Progress-Bar, Tool-Status-Liste, Phase-Indikator |
| `frontend/src/components/scans/ScanTimeline.tsx` | Timeline der Tool-Ausführungen |
| `frontend/src/store/scanStore.ts` | Live-State für laufende Scans |
| `frontend/src/pages/ScanView.tsx` | Progress-Komponenten einbinden |

### Implementierung — Frontend

```typescript
// ScanProgress.tsx — Kernlogik
interface ScanEvent {
  event: string;
  scan_id: string;
  data: {
    tool?: string;
    target?: string;
    phase?: string;
    findings_count?: number;
    status?: string;
    duration?: number;
  };
}

// Events verarbeiten:
// "scan.started"    → Progress 0%, Status "Running"
// "phase.started"   → Phase-Indikator updaten
// "tool.started"    → Tool in Liste als "running" markieren
// "tool.completed"  → Tool als "done" markieren, Findings-Count anzeigen
// "phase.completed" → Progress hochzählen (Phasen / Total Phasen)
// "scan.completed"  → Progress 100%, Confetti 🎉
// "scan.failed"     → Error-State anzeigen
```

Progress-Berechnung: `completedPhases / totalPhases * 100`

### Abhängigkeiten
- **Benötigt:** P1 (Events müssen gesendet werden)
- **Voraussetzung für:** P10 (Notifications bei Completion)

### Akzeptanzkriterien
- [ ] WebSocket verbindet sich automatisch beim Öffnen der Scan-Detail-Seite
- [ ] Progress-Bar zeigt Phase-Fortschritt in Echtzeit
- [ ] Tool-Liste zeigt Status pro Tool (pending/running/completed/failed)
- [ ] Abgeschlossene Tools zeigen Findings-Count + Duration
- [ ] Auto-Reconnect bei WebSocket-Disconnect
- [ ] Scan-Completion Event aktualisiert Scan-Liste automatisch

---

## P10: Notification System

**Status:** `notificationStore.ts` existiert im Frontend.

### Dateien — Backend

| Datei | Änderung |
|-------|----------|
| `backend/app/services/notification_service.py` | **Neu:** Email-Versand bei Scan-Abschluss (optional) |
| `backend/app/core/events.py` | Notification-Trigger bei `scan.completed` / `scan.failed` |
| `backend/app/config.py` | SMTP-Settings: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` |
| `backend/app/models/user.py` | `notification_preferences: JSONB` (email_on_scan_complete, etc.) |

### Dateien — Frontend

| Datei | Änderung |
|-------|----------|
| `frontend/src/store/notificationStore.ts` | Toast-Notifications aus WebSocket Events |
| `frontend/src/components/common/ToastContainer.tsx` | **Neu:** Toast-UI-Komponente |
| `frontend/src/components/layout/MainLayout.tsx` | ToastContainer einbinden |
| `frontend/src/pages/Settings.tsx` | Notification-Preferences (Email on/off) |

### Implementierung — Frontend

```typescript
// notificationStore.ts
interface Notification {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
}

// WebSocket Event → Toast:
// "scan.completed" → success Toast: "Scan 'Quick Recon' abgeschlossen — 12 Findings"
// "scan.failed"    → error Toast: "Scan fehlgeschlagen: ..."
```

### Implementierung — Backend (Email)

```python
# notification_service.py
import smtplib
from email.mime.text import MIMEText

async def send_scan_completion_email(user_email: str, scan_name: str, findings_count: int):
    if not settings.SMTP_HOST:
        return  # Email disabled
    
    msg = MIMEText(f"Scan '{scan_name}' abgeschlossen.\n{findings_count} Findings gefunden.")
    msg["Subject"] = f"ReconForge: Scan '{scan_name}' complete"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = user_email
    
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
```

### Abhängigkeiten
- **Benötigt:** P9 (WebSocket Events)
- **Optional:** SMTP-Server für Email

### Akzeptanzkriterien
- [ ] Toast-Notification bei Scan-Abschluss im Frontend
- [ ] Toast bei Scan-Fehler (rot)
- [ ] Notification-Bell/Badge in Header mit ungelesenen Count
- [ ] Email-Benachrichtigung bei Scan-Abschluss (wenn SMTP konfiguriert)
- [ ] User kann Email-Notifications in Settings ein/ausschalten
- [ ] Notifications verschwinden nach 10s oder bei Click

---

## Parallelisierungs-Matrix

```
Woche 1:
  Python-Dev:  ████ P1 (Scan Dispatch) ████████████████████
  React-Dev:   ████ P9 (WebSocket UI) █████████████████████
  DevOps:      ██ P6 (Logging) ██  ██ P5 (Health) ████████

Woche 2:
  Python-Dev:  ████ P2 (Auto-Discover) ██  ██ P3 (Parsing) ██
  React-Dev:   ████ P10 (Notifications) ██  ██ P8 (Report UI) 
  DevOps:      ██ P4 (Smoke Tests) ██  ██ P7 (DB Backup) ████

Woche 3:
  Python-Dev:  ████ P8 (Report Backend) ████████████████████
  React-Dev:   ████ P8 (Report UI polish) █████████████████
  DevOps:      ████ Integration Testing ████████████████████
```

---

## Risiken

| Risiko | Mitigation |
|--------|-----------|
| Security-Tools nicht im Docker-Image installiert | Dockerfile prüfen, `check_tools.sh` im CI |
| Celery Worker hat keinen Event-Loop für async | Existierender Code nutzt `asyncio.new_event_loop()` — funktioniert |
| WeasyPrint braucht System-Dependencies (Cairo, Pango) | `apt-get install libcairo2 libpango-1.0-0` im Dockerfile |
| Tool-Execution dauert zu lange im CI | Mock-basierte Tests für CI, echte Tool-Tests nur manuell/nightly |
| WebSocket-Events gehen verloren bei Reconnect | Frontend: Missed Events via REST-API nachfragen (`GET /scans/{id}/events`) |
