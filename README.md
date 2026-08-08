# FreelanceHub — Combined Project (Frontend + Backend)

Your project already had a real, working Flask + MySQL backend (auth, projects,
bids, messages, payments, reviews, admin) that renders its own HTML pages. What
was missing was a proper public homepage and the polished branding/logo you
designed separately. This package merges the two:

- Added a real marketing homepage at `/` (`templates/landing.html`), built from
  your polished frontend mockup, linking to the working `/login` and
  `/register` pages instead of just redirecting.
- Added your logo (`backend/static/img/logo.png`) to the homepage, login,
  register, dashboard, and find-work pages.
- Everything else (API routes, database models, JWT auth, dashboard, find-work,
  project/bid/message/payment flows) is your original backend, unchanged and
  still fully wired to its JavaScript `fetch()` calls.

## How the pages fit together

| URL              | Template                        | Notes |
|-------------------|----------------------------------|-------|
| `/`               | `landing.html`                  | Public marketing homepage (new) |
| `/login`          | `auth/login.html`                | Calls `POST /api/auth/login` |
| `/register`       | `auth/register.html`             | Calls `POST /api/auth/register` |
| `/dashboard`      | `dashboard.html`                 | Role-based (client/freelancer/admin) |
| `/find-work`      | `find_work.html`                 | Browse & bid on open projects |
| `/projects/<id>`  | `project_detail.html`            | Existing |
| `/messages/<id>`  | `messages.html`                  | Existing |
| `/payments/<id>`  | `payment.html`                   | Existing |
| `/admin`          | `admin.html`                     | Existing |

## Running it locally

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then edit DB credentials, SECRET_KEY, JWT_SECRET_KEY
mysql -u root -p < schema.sql    # creates the freelancehub database/tables

python app.py
```

Then open **http://localhost:5000/** — you'll land on the new homepage, and
"Join Now" / "Log In" take you into the real, working app.

## Notes
- The database must be MySQL (per `config.py`). If you don't have MySQL
  installed, set `DATABASE_URL` in `.env` to a SQLite URL instead
  (e.g. `sqlite:///freelancehub.db`) for local testing.
- No design/logic in the controllers, services, or routes was changed —
  only templates and the `/` route.
