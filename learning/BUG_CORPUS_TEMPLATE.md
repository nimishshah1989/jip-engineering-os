# Bug Corpus — JIP Platform
# Claude greps this by Category BEFORE writing code.
# Appended automatically after every captured bug fix.
---

[2024-Q4] mfapi.in null returns on delisted funds
Project: MF Pulse | Language: Python | Category: external-api
Bug: Accessing ['data'][0] without null check. Delisted funds return None → AttributeError.
Fix: if data is None or not data.get('data'): return None  # always check first
Root cause: Assumed external API always returns valid data. Never assume.

---
[2024-Q4] Float precision on financial calculations
Project: All JIP | Language: Python | Category: financial-data
Bug: float for NAV/price → 1234.50 * 100 = 123449.9999... Compounds across operations.
Fix: from decimal import Decimal; value = Decimal(str(raw))  # always via str()
Root cause: Python float IEEE 754 cannot represent all decimals exactly.

---
[2025-Q1] India Horizon composite scorer — wrong rescaling
Project: India Horizon | Language: Python | Category: scoring
Bug: Linear rescaling compressed top stocks — all scored ~70-75, indistinguishable.
Fix: Piecewise-linear at P25/P50/P75/P90 breakpoints. Each segment maps to wider output range.
Root cause: Assumed normal distribution. Indian mid/small-cap scores are right-skewed.

---
[2025-Q1] CORS from separate Docker containers
Project: JIP Platform | Language: Docker/Nginx | Category: architecture
Bug: Next.js on port 3000 + FastAPI on port 8000 = different origins = CORS blocked in prod.
Fix: Single Docker Compose, both services inside one container, Nginx reverse proxy internally.
     API_BASE_URL=http://backend:8000 (Docker service name, not localhost).
Root cause: Cross-origin requests blocked by browser even on same physical server.

---
[2025-Q1] Supabase service_role_key exposed client-side
Project: JIP Platform | Language: TypeScript | Category: security
Bug: NEXT_PUBLIC_SUPABASE_SERVICE_KEY exposes full DB access to anyone viewing source.
Fix: service_role_key in .env only, server-side only. Client uses anon_key.
     No NEXT_PUBLIC_ prefix on any secret — ever.
Root cause: Confused which env vars need browser access in Next.js.

---
[2025-Q1] Indian number formatting inconsistency
Project: All JIP frontend | Language: TypeScript | Category: domain-formatting
Bug: .toLocaleString('en-IN') behaves differently on Chrome/Safari/Firefox.
     Same value → ₹12,50,000 on Chrome, ₹1,250,000 on Safari.
Fix: Always use Intl.NumberFormat explicitly or formatLakhs() from utils/format.ts.
Root cause: Browser locale differences — toLocaleString is not reliable cross-platform.

---
[2025-Q1] FastAPI starts with missing env vars
Project: All JIP backend | Language: Python | Category: config
Bug: os.getenv() returns None silently. App starts, fails later with cryptic AttributeError.
Fix: pydantic-settings BaseSettings — settings = Settings() raises ValidationError at startup.
Root cause: Manual getenv() doesn't validate presence. Pydantic does.
