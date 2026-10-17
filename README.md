# MedRoute AI

"Find the Right Doctor. Plan the Right Visit."

A field intelligence platform for Medical Representatives (MRs): doctor/medical-shop/stockist
directories, admin approval workflow, territory-based access control, Google Places discovery,
AI-ranked daily plans, visit tracking with route optimization, and a free map view.

> **Status: backend verified, frontend verified in a browser harness.**
> - Backend: `alembic upgrade head` applied on PostgreSQL 16, the seed and bootstrap scripts
>   run, and the **pytest suite passes (48 tests)**. The live API was exercised end-to-end.
> - Frontend: every page was rendered in Chromium against the live API and the main flows
>   were clicked through (login, maps, discovery, visit planning, route, global search,
>   mobile bottom nav). That run used a React 19 + esbuild harness because `next` itself
>   couldn't be downloaded in the build environment. **Run `npm install && npm run build`
>   once on your machine** as the final check of the real Next.js build.
> - Google Places was tested with recorded (mocked) Places API (New) responses, not a live key.

---

## 1. Architecture

```
medroute-ai/
├── backend/     FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL + Alembic
├── frontend/    Next.js (App Router, JavaScript only) + Tailwind + TanStack Query
├── docs/
├── docker-compose.yml
└── README.md (this file)
```

Backend layering: `api/v1` (thin routers) → `services` (domain logic) → `models` (SQLAlchemy).
Frontend layering: `app/` (routes/pages) → `features` / `components` (UI) → `services` (API calls)
→ `lib/api-client.js` (single fetch wrapper with token refresh).

## 2. Technology stack

- **Frontend:** Next.js (App Router), React, JavaScript only (no TypeScript), Tailwind CSS,
  TanStack Query, React Hook Form + Zod, Lucide icons.
- **Backend:** Python, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Pydantic v2, Alembic,
  python-jose (JWT), bcrypt, Uvicorn, pytest.

## 3. Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+ (or Docker)
- (Optional) Docker + Docker Compose

## 4. Backend setup (manual, without Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env: set DATABASE_URL to a real Postgres connection string and
# generate a real JWT_SECRET, e.g.:
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Create the database (adjust to your Postgres setup)
createdb medroute

# Run migrations
alembic upgrade head

# Seed demo data (development only — refuses to run with APP_ENV=production)
python -m app.seed

# Start the API
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs (Swagger) and http://localhost:8000/redoc.

## 5. Frontend setup (manual)

```bash
cd frontend
npm install
cp .env.example .env.local     # NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
npm run dev
```

App: http://localhost:3000

## 6. Docker Compose (all three services)

```bash
cp backend/.env.example backend/.env      # fill in JWT_SECRET
cp frontend/.env.example frontend/.env
docker compose up --build
```

This starts Postgres, runs `alembic upgrade head` and `python -m app.bootstrap` automatically
(compose sets `SEED_DEMO_DATA=true`, so the demo accounts below are created), then starts the
backend and frontend with hot reload (`frontend/Dockerfile.dev`).

## 7. Testing

```bash
cd backend
# Tests need a real, throwaway Postgres database (Postgres-only types: UUID, ENUM, JSONB).
# The tests create and drop all tables — never point this at real data.
createdb medroute_test
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost/medroute_test
export JWT_SECRET=test-secret
pytest
```

48 tests, all passing: auth and token rotation, MR approval, territory isolation, AI ranking,
visits (duplicates, ownership, missed visits, GPS-start routes), Google discovery
(Places API (New), mocked), global search, analytics, CSV import/export, notifications,
dashboards, the first-run bootstrap, and CORS headers on 500s.

## 8. Authentication & roles

Roles: `SUPER_ADMIN`, `ADMIN`, `MR`. Statuses: `PENDING`, `APPROVED`, `REJECTED`, `SUSPENDED`,
`INACTIVE`. MRs self-register as `PENDING` and need admin approval before they can log in.
Access tokens are short-lived JWTs; refresh tokens are opaque, DB-backed, and rotated (the old
one is revoked) on every `/auth/refresh` call, so a stolen refresh token can only be used once
before rotation invalidates it.

**Backend-enforced, not just frontend:** every protected endpoint depends on
`get_current_user` / `require_admin` / `get_current_approved_mr` in `core/dependencies.py`.
Territory-based data access for MRs (doctors/shops/stockists) is filtered server-side in
`doctor_service.get_mr_authorized_area_names()` — an MR cannot widen this by editing query
params, since the restriction is applied regardless of what the client sends.

## 9. Demo credentials (development seed data only)

| Role | Email | Password |
|---|---|---|
| Super Admin | `superadmin@medroute.dev` | `Demo@1234` |
| Admin | `admin@medroute.dev` | `Demo@1234` |
| MR (approved) | `mr1.approved@medroute.dev` | `Demo@1234` |
| MR (pending) | `mr3.pending@medroute.dev` | `Demo@1234` |
| MR (suspended) | `mr5.suspended@medroute.dev` | `Demo@1234` |

These only exist when the demo data is loaded (`python -m app.seed`, or `SEED_DEMO_DATA=true`
outside production). In production, create your first admin with `INITIAL_ADMIN_EMAIL` /
`INITIAL_ADMIN_PASSWORD` (see "Deploying" below) — never use these demo values.

## 10. What's implemented

- Full auth flow: register, login, refresh rotation, logout, `/auth/me`.
- MR approval workflow: pending → approved/rejected/suspended/reactivated, with audit logging.
- Doctor, Medical Shop, Stockist: full admin CRUD + soft deactivate/reactivate; MR read-only,
  territory-restricted discovery views.
- City → Area → Territory hierarchy; MR↔Territory many-to-many assignment.
- Admin dashboard and MR dashboard, both backed by real DB counts (no fake analytics).
- Audit log with all actions listed in the spec, filterable admin page.
- Health checks (`/health`, `/health/live`, `/health/ready`).
- Consistent `{success, message, data, errors}` API envelope and pagination shape.
- Phase 2–5 placeholders that are *not* wired up: `external_provider` / `external_place_id`
  fields on Doctor/Shop/Stockist, and abstract service interfaces in
  `app/services/future_interfaces.py` (`GooglePlacesService`, `AIRecommendationService`,
  `RouteOptimizationService`, `VisitService`, `NotificationService`).

## 11. Known limitations

1. **Rate limiting is process-local** (slowapi, in-memory). Fine for one backend instance; with
   several replicas use a shared store (e.g. Redis).
2. **Frontend route guards are UX only** by design — real enforcement is the backend
   dependency layer.
3. **No image/file upload** for doctor photos etc.
4. **Notifications are in-app only** — email/SMS/push need a provider and credentials.
5. **Route distances are straight-line** (haversine). "Navigate in Google Maps" opens real
   turn-by-turn directions with traffic — free, no API key.
6. **Map tiles come from the public OpenStreetMap servers.** Fine for normal use; for heavy
   traffic switch `TILE_URL` in `features/doctors/DoctorsMap.jsx` to a hosted tile provider.

## 12. Phase 2 — Google Places integration (Places API (New); tested with mocked responses)

Built on top of Phase 1 without modifying any Phase 1 table:

- **New table:** `place_enrichments` — a cache of Google Places data (rating, review count,
  opening hours, photos, capped reviews), keyed by `(entity_type, entity_id)` so it can cover
  Doctor/MedicalShop/Stockist without three near-identical tables. Migration:
  `alembic/versions/0002_phase2_google_places.py`.
- **Concrete service:** `app/services/google_places_service.py` (`HttpxGooglePlacesService`) —
  calls **Places API (New)** (`places:searchText`, `places/{id}`) and normalizes the
  responses to the legacy field names the rest of the app uses. Implements the `GooglePlacesService`
  abstract contract that Phase 1 defined in `app/services/future_interfaces.py`.
- **Orchestration:** `app/services/external_data_service.py` — reads always hit our cache, never
  Google; writes only happen via an explicit admin action (`POST /doctors/{id}/sync-external`),
  since Google Places has real per-call cost/quota. Failures are recorded as audit log entries
  (`EXTERNAL_SYNC_FAILED`) rather than silently swallowed or faked.
- **New endpoints:** `GET /doctors/{id}/external-data` (Admin + territory-authorized MR, returns
  `data: null` if never synced — never fabricated), `POST /doctors/{id}/sync-external` (Admin only).
- **Frontend:** MR doctor profile now shows real rating/reviews/opening hours when synced, or an
  honest "Not yet synced from Google" message otherwise; admin doctor edit page has a
  "Sync from Google" button.
- **Config:** `GOOGLE_PLACES_ENABLED` and `GOOGLE_PLACES_API_KEY` in `backend/.env`. With
  `GOOGLE_PLACES_ENABLED=false` (the default), sync returns a clear `503` rather than pretending
  to work.
- **Tests:** `tests/test_external_data.py` (sync, service methods mocked) and
  `tests/test_discovery.py` (search/import, HTTP layer mocked with Places API (New)-shaped
  payloads — so request URLs, headers, field masks and response parsing are covered).
  The first call with a real key is the final check; if Google rejects it, the admin sees
  Google's own error message.

## 13. Phase 3 — AI recommendation engine (rule-based, no external AI API)

**Important framing:** this is a deterministic, explainable scoring formula over real DB data —
not a call to an LLM or ML model. Two reasons: this sandbox has no network access to call any
external AI API, and a transparent formula is arguably the right choice for a "why this doctor?"
feature MRs need to trust, over an opaque black-box score.

- **Service:** `app/services/ai_recommendation_service.py` (`RuleBasedAIRecommendationService`,
  implementing the Phase 1 `AIRecommendationService` contract — extended to take an `AsyncSession`
  per call since the original abstract stub predated any DB wiring; documented in the file).
- **Scoring inputs (0–100 total, capped):** a flat base score for being an active doctor in the
  MR's territory; up to 40 points from Google rating + review volume **if and only if** the
  doctor has been synced via Phase 2 (unsynced doctors just don't get this component — no
  fabricated ratings); up to 30 points from profile completeness (phone/email/clinic/hospital/
  qualification present); 15 points if added to the directory in the last 30 days. Every point
  awarded has a matching plain-language "reason" string — nothing in the "why" is invented after
  the score is computed.
- **New endpoints:** `GET /ai/daily-plan` (MR's own territory, ranked, limit configurable) and
  `GET /ai/doctors/{id}/opportunity-score` (Admin unrestricted, MR territory-restricted — 404s,
  not 403, for an out-of-territory doctor, consistent with how doctor detail already behaves).
- **Frontend:** MR dashboard now shows a real top-3 preview instead of a "coming in Phase 3"
  placeholder; new `/mr/ai/daily-plan` page with the full ranked list and reasons; doctor profile
  shows a real "AI Opportunity" score card instead of a placeholder.
- **Tests:** `tests/test_ai_recommendations.py` — verifies territory isolation (an MR's daily
  plan never includes a doctor outside their assigned area) and that a more complete profile
  scores strictly higher than a bare one. Like everything else, **not run** against a live
  database in this environment.

## 14. Phase 4 — visit management, follow-ups, route optimization

- **New table:** `visits` (`mr_id`, `doctor_id`, `scheduled_date`, `status`, `notes`, `outcome`,
  `follow_up_date`) — one row per planned/completed visit, unique on
  `(mr_id, doctor_id, scheduled_date)` so the same doctor can't be double-booked the same day.
  Migration: `alembic/versions/0003_phase4_visits.py`.
- **"Add to Visit Plan" is now live** — the disabled Phase 1 button on the doctor discovery card
  calls `POST /visits`, which re-checks the doctor is inside the MR's own territory before
  creating the row (same enforcement pattern as everywhere else — 404, not 403, for anything
  outside the MR's assignment).
- **Visit lifecycle:** `PUT /visits/{id}` marks a visit COMPLETED/CANCELLED/MISSED with notes,
  outcome, and an optional follow-up date. Ownership is enforced — an MR can only ever touch
  their own visits (`get_own_visit` 404s otherwise, never revealing another MR's visit exists).
- **Route optimization — the one part of this project actually run and verified in this
  environment:** `app/services/route_optimization_pure.py` contains a pure, dependency-free
  haversine-distance + nearest-neighbor algorithm with a `if __name__ == "__main__"` self-check.
  Run it yourself with zero setup:
  ```bash
  cd backend && python3 app/services/route_optimization_pure.py
  ```
  This is a real greedy TSP heuristic (not a call to any routing API) — correct for a day's
  handful of stops, not claiming global optimality. `route_optimization_service.py` wraps it
  with a DB lookup of doctor coordinates for `GET /visits/daily-route`.
- **Follow-ups:** `GET /visits/follow-ups` returns all upcoming follow-up dates for the MR,
  surfaced on the doctor profile page.
- **Doctor profile:** "Visit History" and "Follow-ups" are no longer placeholders — they show
  the requesting MR's own real visit history with that doctor.
- **New frontend pages:** `/mr/visits` (list + mark complete/cancel), `/mr/visits/route`
  (date-pickable optimized daily route).
- **Seed data updated** with real Lucknow-area coordinates on demo doctors so the route feature
  has something meaningful to order out of the box.
- **Tests:** `tests/test_visits.py` — territory enforcement, duplicate-visit prevention,
  cross-MR ownership isolation, and a route-ordering test using real coordinates (Lucknow ×2 +
  Delhi, asserting Delhi ends up last). Endpoint tests still need a live Postgres to actually
  run; the pure algorithm test above does not and was genuinely executed.

## 15. Phase 5 — analytics, bulk import/export, notifications

- **Analytics (`app/services/analytics_service.py`):** MR performance (visits planned/completed/
  cancelled/missed, completion rate, distinct doctors covered, last visit date) and territory
  coverage (% of a territory's active doctors with at least one completed visit). Every number
  comes straight from `visits`/`doctors` rows — an MR or territory with zero visits reports zero,
  never an interpolated or placeholder figure. New page: `/admin/analytics`.
- **Bulk import/export (`app/services/bulk_import_service.py`):** `GET /doctors/export` streams
  a real CSV of the current doctor directory; `POST /doctors/import` parses an uploaded CSV
  (Python's stdlib `csv` module — no external dependency), matches each row's `specialization`
  column to an existing `Specialization` by name, and reports per-row errors rather than
  rejecting the whole file for one bad row. Imported doctors get `source=IMPORT` — a value
  Phase 1 defined for exactly this. Registered *before* the `/{doctor_id}` route in
  `doctors.py`, since a literal path like `/doctors/export` would otherwise be swallowed by the
  dynamic UUID route (a real bug caught and fixed while building this — documented in the
  router's comments).
- **Notifications (`app/models/notification.py`, `app/services/notification_service.py`):** a
  real in-app notification table, not a stub. Hooked into MR approval/rejection/suspension and
  territory assignment — an MR gets an actual row created the moment an admin acts, not a
  polling simulation. Topbar bell is now functional: unread badge, dropdown, mark-as-read,
  mark-all-read.
- **Tests:** `tests/test_phase5.py` covers zero-data analytics correctness, CSV import row-level
  validation (good row created, bad specialization skipped, missing field skipped, with matching
  error messages), CSV export content, and the approval → notification → read flow.

### What's still a stub after all five phases

- `NotificationService`'s *external* channels (email/SMS/push) are not implemented — only
  in-app notifications. Wiring a real email provider needs credentials and network access this
  environment doesn't have.
- No scheduler: past PLANNED visits are flagged MISSED lazily, whenever visits or analytics
  are read. A daily follow-up digest would need a scheduler (APScheduler, or a cron job
  calling an endpoint).
- Google Places sync (Phase 2) and the rule-based AI score (Phase 3) still don't talk to each
  other beyond the score reading cached Places data — there's no cross-entity intelligence
  (e.g. "doctors near your top-scored doctor").

## 16. Doctor Discovery from Google Places + Map View (added post-launch)

Two additions on top of Phase 2's enrichment sync:

- **Free map view (no API key needed):** `/mr/doctors`, `/admin/doctors`, the MR doctor
  profile, the discovery results and the daily route all have maps. The map uses **Leaflet + OpenStreetMap tiles** — free, no Google Maps key, no billing —
  plotting every doctor that already has `latitude`/`longitude` on file. See
  `frontend/features/doctors/DoctorsMap.jsx`.
- **"Discover from Google" (real doctor data, needs your own API key):** `/admin/doctors/discover`
  lets an admin search Google Places by specialization + area/city/state and import real,
  verified doctors — replacing manually-entered or seed/demo rows. Two-step and explicit by
  design: search returns candidates only, nothing is written to the DB until the admin clicks
  "Import" on a specific one. Imported doctors get `source=EXTERNAL` and their Places rating/
  reviews/hours are cached immediately (same `place_enrichments` table Phase 2 uses).
  - **Requires** `GOOGLE_PLACES_ENABLED=true` and a real `GOOGLE_PLACES_API_KEY` with
    **Places API (New)** enabled and a billing account linked. Without it, the search endpoint
    returns a clear 503 and the page shows setup steps — never fake data.
  - Backend: `app/services/discovery_service.py`, `app/api/v1/doctor_discovery.py`.
  - **We do not scrape Google/social media directly** — this only ever calls the official,
    ToS-compliant Google Places API. Scraping would violate platform terms and risks importing
    unverified/stale data as if it were confirmed.
- **Mobile bottom nav for MR:** a fixed bottom tab bar (Home/Doctors/AI Plan/Visits/Profile)
  appears on phone-width screens, since MRs are primarily mobile per the original spec. See
  `frontend/components/layout/MobileBottomNav.jsx`.

### New dependency
`frontend/package.json` now includes `leaflet` (used directly — no `react-leaflet`, so there
are no React-version peer conflicts and nothing touches `window` during server rendering).
Run `npm install` again after pulling this change.

## 17. October 2026 hardening pass — what changed

**Fixed bugs (each one now has a test):**
- `GET /admin/dashboard` and `GET /territories/mine` returned 500 (`MissingGreenlet`: async
  lazy-loading during serialization). Admin dashboard, MR Territories and MR Profile pages
  were broken.
- 500 responses carried no CORS headers, so browsers reported a misleading "blocked by CORS
  policy". Errors are now caught inside the CORS middleware.
- The doctor-discovery router was never registered — `/doctors/discovery/*` was a 404.
- The Google client used the **legacy** Places API, which new Google Cloud projects can no
  longer enable. It now uses **Places API (New)** and normalizes responses to the same shape,
  so cached data and the UI are unchanged. An import makes 1 Google call instead of 2.
  Duplicate imports return 409, an unknown specialization returns 404 instead of 500, and
  Google's own error message (e.g. "API key not valid") is shown to the admin.
- Planning the same doctor twice on one day returned 500 instead of 409.
- Daily route started from an arbitrary stop (DB row order). It now starts from the first
  planned visit, or from the MR's GPS position (`start_lat`/`start_lng`), and returns
  per-stop distances.
- Two access tokens minted in the same second were identical (added a `jti`).
- `passlib` is unmaintained and breaks with bcrypt ≥ 4.1; replaced with direct `bcrypt`.
  Existing password hashes keep working.
- bcrypt ran on the event loop, freezing every other request during a login; it now runs in
  a worker thread. Failed logins for unknown emails now take the same time as for real ones.
- Refresh-token lookup was O(n) bcrypt checks; it's now an indexed HMAC-SHA256 lookup
  (migration `0005` revokes old-format tokens, so users log in once more).
- The frontend fired one `/auth/refresh` per failed request when the access token expired;
  refresh tokens are single-use, so parallel requests logged the user out. Refresh is now
  shared.
- "Today" used the UTC date in the browser (wrong before 5:30 AM IST); dates are now local,
  and the backend uses `APP_TIMEZONE` (default `Asia/Kolkata`).
- Toasts crashed on plain-http LAN URLs (`crypto.randomUUID` needs a secure context).
- The backend Docker image ran the demo seed on **every start, including production**,
  creating `Demo@1234` super-admin accounts. Replaced by `python -m app.bootstrap` (see below).
- Model/migration drift on `territory_mrs.assigned_at`; `alembic check` is now clean.

**New features:**
- Global search in the topbar (`GET /search`): doctors, shops, stockists, plus MRs for
  admins; territory-restricted for MRs; mobile search panel.
- `/admin/doctors/discover` page: search Google, see results on a map, import with one click.
- Daily Route: "Start from my location", per-stop and total km, route on the map, and a
  "Navigate in Google Maps" button with all stops as waypoints.
- MR mobile bottom navigation; Leaflet maps on the doctor lists and the doctor profile.
- Visit plan date picker on doctor cards; "Add to today" on the AI Daily Plan.
- My Visits shows the doctor's name. Past PLANNED visits automatically become MISSED (so
  analytics "missed" is real), and a missed visit can still be logged as completed.
- Territories page shows MR names instead of raw IDs.
- `DATABASE_URL` accepts `postgres://…?sslmode=require` URLs from Render/Neon/Supabase as-is.
- With `APP_ENV=production` the app refuses to start with a weak or default `JWT_SECRET`.

## 18. Deploying (e.g. Render)

**Backend** (Docker, root directory `backend`): set these environment variables:

| Variable | Value |
|---|---|
| `APP_ENV` | `production` |
| `DATABASE_URL` | your Postgres URL (`postgres://…` from Render/Neon is fine as-is) |
| `JWT_SECRET` | `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `CORS_ORIGINS` | your frontend URL, e.g. `https://medroute-web.onrender.com` |
| `INITIAL_ADMIN_EMAIL` / `INITIAL_ADMIN_PASSWORD` | your first super-admin login (created once) |
| `GOOGLE_PLACES_ENABLED` / `GOOGLE_PLACES_API_KEY` | optional, for Discover from Google |

On start the container runs migrations, then `app.bootstrap`, then uvicorn on `$PORT`.

**Frontend** (Docker, root directory `frontend`): pass the API URL **at build time**, since
Next.js bakes `NEXT_PUBLIC_*` into the bundle — e.g. a build argument / env var
`NEXT_PUBLIC_API_URL=https://<your-backend>/api/v1`. The image runs `next start` on `$PORT`.

**Upgrading an existing deployment:** demo accounts created by the old image stay in the
database. Log in with your new `INITIAL_ADMIN_*` admin and suspend or delete them (or change
their passwords) — `Demo@1234` is public in this README.

## 19. Explore any area (free — no API key)

`/mr/explore` and `/admin/explore` let anyone search doctors & clinics, hospitals, medical
stores or distributors around **any** place (typed area/city/pincode, or "Near me" GPS),
not just the MR's territory.

- Data: **OpenStreetMap** — Nominatim for the place name, Overpass for the listings
  (`app/services/explore_service.py`, `GET /api/v1/explore/places`). Free, no key, no billing.
- Each result shows distance, speciality, address, phone (tap to call), opening hours,
  **Directions** and **Reviews on Google** links.
- **"Full list with ratings on Google Maps"** opens the same search in Google Maps, which
  shows every Google Business Profile with ratings and reviews. It's a plain link, so it is
  free — no Places API call is made.
- Fair use: results are cached (1 h search, 24 h geocoding), Nominatim is called at most once
  a second, and the endpoint is rate-limited (`EXPLORE_RATE_LIMIT`, default 20/minute).
  Set `OSM_CONTACT_EMAIL` so the public OSM services can identify the app.
- OpenStreetMap has fewer listings than Google in some areas and no ratings — that's what
  the Google Maps button is for.
