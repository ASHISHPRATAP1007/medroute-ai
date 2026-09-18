# MedRoute AI — Phase 1

"Find the Right Doctor. Plan the Right Visit."

A field intelligence platform for Medical Representatives (MRs): doctor/medical-shop/stockist
directories, admin approval workflow, and territory-based access control.

> **Status: written, not yet run.** This code was generated in a sandboxed environment with
> no network access and no PostgreSQL instance available, so it has **not** been installed,
> started, or tested end-to-end. Every backend file passed a Python `py_compile` syntax check,
> but that only proves the files parse — it does not prove the app runs. Follow the steps below
> on your own machine and treat the first `alembic upgrade head` / `npm run dev` / `pytest` run
> as the real first test. See **"Known limitations"** at the bottom before relying on this.

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
  python-jose (JWT), passlib/bcrypt, Uvicorn, pytest.

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

# Seed demo data
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

This starts Postgres, runs `alembic upgrade head` automatically, then starts the backend and
frontend. Run the seed script once the backend container is healthy:

```bash
docker compose exec backend python -m app.seed
```

## 7. Testing

```bash
cd backend
# Tests need a real Postgres database (Postgres-only types: UUID, ENUM, INET)
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost/medroute_test
export JWT_SECRET=test-secret
pytest
```

**Not yet run in this environment** (no Postgres available). Written tests cover: registration,
login, pending/suspended access rules, refresh-token rotation, MR approval/authorization,
admin-vs-MR access boundaries.

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

Never use these values in a production deployment.

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

## 11. Known limitations (read before relying on this)

1. **Never executed.** No `pip install`, `npm install`, `alembic upgrade head`, `pytest`, or
   `npm run build` has been run against this code in the environment that produced it (no
   network access, no PostgreSQL). Expect to fix minor issues on first run — dependency version
   pins may need adjusting, and the hand-written Alembic migration (`0001_initial.py`) was
   written to mirror the SQLAlchemy models exactly but was never applied to a real database.
2. **Refresh-token lookup is O(n).** `rotate_refresh_token` in `auth_service.py` scans all
   non-revoked refresh tokens and bcrypt-verifies each one, since tokens are stored hashed and
   can't be looked up by equality. Fine for demo data volumes; before production scale, either
   index on a partial token prefix or store refresh tokens as a fast HMAC instead of bcrypt.
3. **Rate limiting is process-local** (slowapi, in-memory). Fine for a single instance; won't
   work correctly across multiple backend replicas without a shared store (e.g. Redis).
4. **Frontend route guards are UX only,** as required by the spec — real enforcement is the
   backend dependency layer. This is by design, not an oversight.
5. **No image/file upload** for doctor photos etc. — out of scope for Phase 1 per spec.
6. **Global search (spec §30)** is a static input in the topbar with no backend wiring yet —
   the grouped-results search endpoint itself was not built out in this pass.
7. **Frontend was not lint/build-checked** the way the backend was syntax-checked, because
   `npm install` requires network access unavailable in this environment.

## 12. Phase 2 — Google Places integration (implemented, unverified against live Google API)

Built on top of Phase 1 without modifying any Phase 1 table:

- **New table:** `place_enrichments` — a cache of Google Places data (rating, review count,
  opening hours, photos, capped reviews), keyed by `(entity_type, entity_id)` so it can cover
  Doctor/MedicalShop/Stockist without three near-identical tables. Migration:
  `alembic/versions/0002_phase2_google_places.py`.
- **Concrete service:** `app/services/google_places_service.py` (`HttpxGooglePlacesService`) —
  calls Google's Find Place / Place Details endpoints. Implements the `GooglePlacesService`
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
- **Tests:** `tests/test_external_data.py` — all Google calls are mocked (`unittest.mock.patch`
  on `HttpxGooglePlacesService`), since there's no network access in this environment to hit the
  real API. **The `HttpxGooglePlacesService` HTTP calls themselves have never been exercised
  against real Google endpoints** — verify request/response field names against
  [Google's current Places API docs](https://developers.google.com/maps/documentation/places/web-service)
  before relying on this in production; Google does change API versions and field names.

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
- No scheduled/background jobs exist anywhere in this codebase (e.g. auto-flagging `MISSED`
  visits after their date passes, or a daily follow-up digest) — everything is computed on
  request. Adding a scheduler (Celery, APScheduler, or a cron-triggered endpoint) is the natural
  next step if this goes further.
- Google Places sync (Phase 2) and the rule-based AI score (Phase 3) still don't talk to each
  other beyond the score reading cached Places data — there's no cross-entity intelligence
  (e.g. "doctors near your top-scored doctor").
