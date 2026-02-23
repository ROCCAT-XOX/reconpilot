# ReconForge — Autonomous Improvement Roadmap

## Test Target
- Domain: `promediaweb.de`
- Contact: `stumpf@promediaweb.de`

## Priority 1 — Bug Fixes & Polish
- [ ] `/api/v1/scans/` returns 404 — needs router registration or trailing slash fix
- [ ] Frontend: verify Scan Wizard renders correctly with new Auto-Discover toggles
- [ ] Clean up test data from live instance after testing
- [ ] Add `backend/e2e_test.db` to `.gitignore`

## Priority 2 — Core Functionality
- [ ] Password change endpoint (`/auth/password`) — Settings page wires to it but it doesn't exist
- [ ] Scan execution: wire Celery tasks to actually run tools (currently scan creates DB entry but doesn't dispatch)
- [ ] Tool output parsing: parse Nmap/Nuclei/etc output into Findings
- [ ] Auto-Discover backend logic: when `auto_discover.subdomains=true`, auto-run Subfinder; when `technologies=true`, auto-run WhatWeb; when `ports=true`, full port scan

## Priority 3 — UX Improvements  
- [ ] Dashboard: real stats from DB (project count, scan count, findings by severity)
- [ ] Findings detail view with evidence/remediation
- [ ] Scan progress: real-time updates via polling or SSE
- [ ] Notification system for scan completion

## Priority 4 — DevOps
- [ ] CI post-deployment smoke tests (curl health + login after deploy)
- [ ] Backup cron for PostgreSQL data
- [ ] Log aggregation / error tracking
