# FreelanceHub Backend

Flask + MySQL (SQLAlchemy ORM) backend for a Fiverr/Upwork-style freelancer marketplace.

Built **module by module**. This delivery covers:

## ✅ Module 1 — Database Schema
All normalized tables defined in `models.py` (mirrored in `schema.sql`):

| Table | Purpose |
|---|---|
| `users` | Core auth + role (client/freelancer/admin) |
| `profiles` | 1-1 extended profile (bio, title, hourly_rate, etc.) |
| `skills` / `freelancer_skills` | Master skill list + many-to-many junction |
| `portfolio_links` | Freelancer portfolio URLs (1-many) |
| `projects` | Client-posted projects |
| `bids` | Freelancer bids on projects |
| `messages` | Chat tied to a project |
| `payments` | Status-only payment tracking (pending/paid/cancelled) |
| `reviews` | Client → freelancer rating & comment |

## ✅ Module 2 — Authentication
- `POST /api/auth/register` — register as client or freelancer (bcrypt-hashed password, auto-creates empty profile)
- `POST /api/auth/login` — returns JWT access + refresh tokens
- `POST /api/auth/logout` — blacklists current access token (requires `Authorization: Bearer <token>`)
- `POST /api/auth/refresh` — exchange refresh token for new access token
- `GET /api/auth/me` — get current logged-in user + profile

Role-based access is enforced via `utils/decorators.py::role_required(*roles)`, which will be used across all future modules (project, bid, chat, review, admin).

## ✅ Module 3 — Profile Management + Project CRUD

**Profiles** (`routes/profile_routes.py`, `controllers/profile_controller.py`, `services/profile_service.py`)
- `GET /api/profile/me` — get your own profile (bio, phone, location, and freelancer fields: title, experience, hourly rate, skills, portfolio)
- `PUT /api/profile/me` — update your profile. Freelancer-only fields (`title`, `experience_years`, `hourly_rate`) are silently ignored for clients.
- `POST /api/profile/skills` — add a skill (freelancer only, body: `{"name": "React"}`)
- `DELETE /api/profile/skills/<skill_id>` — remove a skill (freelancer only)
- `POST /api/profile/portfolio` — add a portfolio link (freelancer only, body: `{"title": "...", "url": "https://..."}`)
- `DELETE /api/profile/portfolio/<link_id>` — remove a portfolio link (freelancer only)
- `GET /api/profile/<user_id>` — view any user's public profile

**Projects** (`routes/project_routes.py`, `controllers/project_controller.py`, `services/project_service.py`)
- `POST /api/projects` — create a project (client only)
- `GET /api/projects` — list/search/filter projects. Query params: `status`, `category`, `keyword`, `budget_min`, `budget_max`, `page`, `per_page`. Freelancers default to `status=open` unless they pass a status explicitly; clients/admins see all statuses by default.
- `GET /api/projects/mine` — client's own projects, any status (client only)
- `GET /api/projects/<id>` — project detail. Bids are included only for the owning client or an admin.
- `PUT /api/projects/<id>` — edit a project (owner only, only while status is `open`)
- `DELETE /api/projects/<id>` — delete a project (owner only, only while `open` and no bids exist yet — cancel instead of delete once bids come in)
- `PATCH /api/projects/<id>/status` — change status (owner only). Allowed transitions: `open → in_progress/cancelled`, `in_progress → completed/cancelled`. Marking `completed` requires an accepted bid (wired up fully once bidding — Module 4 — lands).

Bid-related actions (accept one freelancer, reject other bids, submit/edit/withdraw a bid) live in Module 4 below, since they operate on the `bids` table.

## ✅ Module 4 — Bidding System

`routes/bid_routes.py`, `controllers/bid_controller.py`, `services/bid_service.py`

- `POST /api/bids` — submit a bid (freelancer only). Body: `{"project_id", "price", "proposal", "estimated_days"}`. Rejected if the project isn't `open`, or if this freelancer already has a bid on it (one bid per freelancer per project).
- `GET /api/bids/mine` — freelancer's own bids, optional `?status=` filter, paginated
- `GET /api/bids/accepted-projects` — projects where this freelancer's bid was accepted (freelancer's "My Accepted Projects" view)
- `GET /api/bids/project/<project_id>` — all bids on a project (project owner or admin only)
- `PUT /api/bids/<id>` — edit a bid (freelancer, own bid, only while `pending` and project still `open`)
- `POST /api/bids/<id>/withdraw` — withdraw a bid (freelancer, own bid, only while `pending`)
- `POST /api/bids/<id>/accept` — accept a bid (client, project owner only). This single transaction: marks the bid `accepted`, auto-rejects every other pending bid on that project, moves the project to `in_progress`, and creates its `Payment` record (`pending`, amount = accepted bid price).
- `POST /api/bids/<id>/reject` — reject a single pending bid (client, project owner only) without accepting anyone else yet.

**Design note:** the freelancer-side "update project status" feature is intentionally satisfied by the chat module (Module 5) rather than a redundant status endpoint — once a project is `in_progress`, the freelancer can post updates via chat, while the client retains sole authority to mark `completed`/`cancelled` through `PATCH /api/projects/<id>/status` (Module 3). This avoids two roles racing to mutate the same status field.

## ✅ Module 5 — Chat

`routes/message_routes.py`, `controllers/message_controller.py`, `services/message_service.py`

- `POST /api/messages` — send a message. Body: `{"project_id", "content"}`. Chat unlocks only once the project has an accepted bid; only the client and the accepted freelancer may send/receive.
- `GET /api/messages/project/<project_id>` — full conversation history for a project (participants or admin only). Marks the reader's unread messages as read as a side effect.
- `GET /api/messages/unread-count` — total unread message count for the current user (for a notification badge).

## ✅ Module 6 — Reviews

`routes/review_routes.py`, `controllers/review_controller.py`, `services/review_service.py`

- `POST /api/reviews` — client rates & reviews the freelancer after project completion. Body: `{"project_id", "rating" (1-5), "comment"}`. Requires the project to be `completed` with an accepted freelancer, and allows exactly one review per project (also enforced at the DB level).
- `GET /api/reviews/freelancer/<user_id>` — all reviews received by a freelancer, plus `average_rating` and `total_reviews` — this is how freelancers "receive ratings."
- `GET /api/reviews/project/<project_id>` — the review for one specific project (participants or admin only).

## ✅ Payment Module — Status Tracking (no gateway)

`routes/payment_routes.py`, `controllers/payment_controller.py`, `services/payment_service.py`

- `GET /api/payments/project/<project_id>` — view the payment record for a project (client, the accepted freelancer, or admin).
- `PATCH /api/payments/<id>/status` — update status to `pending` / `paid` / `cancelled` (project's client, or admin). Once a payment is marked `paid`, only an admin can change it further, to prevent accidental reversal. No payment gateway is integrated — this purely tracks state, per spec.

## ✅ Module 7 — Admin

`routes/admin_routes.py`, `controllers/admin_controller.py`, `services/admin_service.py` — every endpoint requires the `admin` role.

- `GET /api/admin/dashboard` — platform stats: user counts by role, project counts by status, bid counts by status, total reviews & average rating, total amount paid, 5 most recent users and projects. This doubles as the "view reports" requirement.
- `GET /api/admin/users` — list/search all users (`?role=`, `?account_status=`, `?keyword=`, paginated)
- `PATCH /api/admin/users/<id>/status` — set `account_status` to `active` / `suspended` / `deleted`
- `DELETE /api/admin/users/<id>` — hard-delete a user (fake account cleanup). Cascades to their profile, projects, bids, etc. per the FK constraints in `schema.sql`. An admin cannot delete their own account this way.
- `GET /api/admin/projects` — list/search all projects regardless of status
- `DELETE /api/admin/projects/<id>` — force-delete any project
- `GET /api/admin/bids` — list/filter all bids platform-wide (`?status=`, `?project_id=`)
- `DELETE /api/admin/bids/<id>` — force-delete any bid

---

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env with your MySQL credentials

mysql -u root -p -e "CREATE DATABASE freelancehub CHARACTER SET utf8mb4;"
# (app.py auto-creates tables via db.create_all() on first run —
#  or run schema.sql manually if you prefer explicit DDL)

python app.py
```

Server runs at `http://localhost:5000`. Health check: `GET /api/health`.

## Example Requests

**Register**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane Doe","email":"jane@example.com","password":"pass123","role":"freelancer"}'
```

**Login**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"jane@example.com","password":"pass123"}'
```

**Authenticated request**
```bash
curl http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer <access_token>"
```

## Response Format
All endpoints return a consistent envelope:
```json
{ "success": true, "message": "...", "data": { ... } }
{ "success": false, "message": "...", "errors": { ... } }
```

---

## Project Status: All 7 Modules Complete

1. ✅ Database schema
2. ✅ Authentication
3. ✅ Profile management + Project CRUD
4. ✅ Bidding system
5. ✅ Chat
6. ✅ Reviews
7. ✅ Admin

Plus the Payment status-tracking module. Every blueprint is registered in `app.py`.

### End-to-end flow this backend supports
1. Client and freelancer register/login (`/api/auth`)
2. Both fill out their profile; freelancer adds skills + portfolio (`/api/profile`)
3. Client posts a project (`/api/projects`)
4. Freelancers browse/search open projects and submit bids (`/api/projects`, `/api/bids`)
5. Client reviews bids on their project and accepts one (`/api/bids/<id>/accept`) — this auto-rejects the rest, flips the project to `in_progress`, and creates a `pending` payment
6. Client and the accepted freelancer chat about the work (`/api/messages`)
7. Client marks the project `completed` (`/api/projects/<id>/status`)
8. Client marks the payment `paid` (`/api/payments/<id>/status`)
9. Client leaves a rating & review for the freelancer (`/api/reviews`)
10. Admin can monitor everything and moderate users/projects/bids at any point (`/api/admin`)

### Suggested next steps (beyond this backend)
- Build the frontend (the `templates/`/`static/` folders and Jinja are scaffolded but unused — a SPA via React/Vue talking to these JSON APIs is a natural fit)
- Add automated tests (`TestingConfig` with in-memory SQLite is already wired in `config.py` for this)
- Add file uploads for profile pictures/portfolio attachments (`UPLOAD_FOLDER` is already configured in `config.py`)
- Add pagination-aware indexes/query tuning once real data volume shows up
- Consider WebSockets (Flask-SocketIO) for real-time chat instead of polling `/api/messages/project/<id>`
