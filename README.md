# Pipeline Release Events API

A small HTTP service for tracking **pipeline release events** — one record per
service deployment, storing the outcome, elapsed pipeline time, and the commit
that triggered the run.

Stack: **FastAPI** + **SQLite**. Each event has the following shape:

```json
{
  "id": "evt_001",
  "service": "payment-service",
  "status": "failed",
  "duration": 275,
  "timestamp": "2025-05-10T09:15:00Z",
  "commit_sha": "f3a9c12b"
}
```

> `duration` — elapsed seconds from pipeline start to terminal state.
> `status` — one of `success`, `failed`, `in_progress`, or `rolled_back`.

---

## Setup

Python 3.10 or newer is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m app.seed          # insert 40 sample events
uvicorn app.main:app --reload
```

Once running, the API is reachable at **http://127.0.0.1:8000**.

The interactive docs at **http://127.0.0.1:8000/docs** let you try every
endpoint directly in the browser.

---

## API reference

| Method | Path                  | What it does                              |
| ------ | --------------------- | ----------------------------------------- |
| `GET`  | `/deployments`        | Return a list of events (filterable).     |
| `GET`  | `/deployments/{id}`   | Return one event by id.                   |

**Listing events** — both filters are optional and can be combined:

```bash
# everything
curl http://127.0.0.1:8000/deployments

# failed releases from payment-service only
curl 'http://127.0.0.1:8000/deployments?service=payment-service&status=failed'
```

The response body is a plain JSON array. The total number of matching records
is returned in the `X-Total-Count` response header.

**Fetching a single event:**

```bash
curl http://127.0.0.1:8000/deployments/evt_001
```

Requesting an id that does not exist returns `404`. Passing an unrecognised
status value returns `422` with a field-level error message.

---

## Tests

```bash
.venv/bin/pytest -v
```

---

## Project layout

```
app/
  api/            HTTP route handlers
  services/       business logic layer
  repositories/   all database queries
  models/         SQLAlchemy ORM definitions
  schemas/        Pydantic response models
  core/           config, logging, error handling, middleware
  data/           engine and session management
tests/            pytest test suite
```

Sample data lives in `events.db`. Run `python -m app.seed` at any time to wipe
and repopulate it with a fresh set of 40 events.
