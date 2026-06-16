"""Load the database with sample pipeline release events.

Run with:  ``python -m app.seed``

Produces a fixed, reproducible set of events covering all six services, every
possible status, and a realistic spread of timestamps and durations. The data
is ready to query immediately after running. Re-running this script wipes and
rebuilds the table from scratch.
"""

import random
from datetime import datetime, timedelta, timezone

from app.data.base import Base
from app.data.session import SessionLocal, engine
from app.models.release_event_model import ReleaseEvent, EventStatus

SERVICES = [
    "payment-service",
    "identity-provider",
    "dashboard-ui",
    "alert-worker",
    "discovery-api",
    "checkout-gateway",
]

# Most pipelines complete successfully. A realistic tail of failures and
# rollbacks gives the filter endpoints something meaningful to return.
OUTCOME_WEIGHTS = {
    EventStatus.SUCCESS: 65,
    EventStatus.FAILED: 20,
    EventStatus.IN_PROGRESS: 5,
    EventStatus.ROLLED_BACK: 10,
}

TOTAL_EVENTS = 40
SEED_VALUE = 7


def generate_seed_data(
    count: int = TOTAL_EVENTS, seed: int = SEED_VALUE
) -> list[ReleaseEvent]:
    """Return a reproducible list of mock release events."""
    rng = random.Random(seed)
    now = datetime.now(timezone.utc)
    outcomes = list(OUTCOME_WEIGHTS)
    weights = list(OUTCOME_WEIGHTS.values())

    events: list[ReleaseEvent] = []
    for idx in range(1, count + 1):
        outcome = rng.choices(outcomes, weights=weights, k=1)[0]

        # Happy-path runs finish quickly; failures and rollbacks take longer;
        # a small fraction of events represent pathologically slow pipelines.
        base_duration = rng.randint(30, 250)
        if outcome in (EventStatus.FAILED, EventStatus.ROLLED_BACK):
            base_duration += rng.randint(80, 350)
        if rng.random() < 0.08:  # ~8% outlier probability
            base_duration += rng.randint(400, 1000)
        duration = (
            base_duration
            if outcome != EventStatus.IN_PROGRESS
            else rng.randint(10, 90)
        )

        # Scatter events randomly over the past 45 days.
        occurred_at = now - timedelta(
            days=rng.randint(0, 44),
            hours=rng.randint(0, 23),
            minutes=rng.randint(0, 59),
        )

        events.append(
            ReleaseEvent(
                id=f"evt_{idx:03d}",
                service=rng.choice(SERVICES),
                status=outcome,
                duration=duration,
                timestamp=occurred_at,
                commit_sha=f"{rng.randrange(16**8):08x}",
            )
        )
    return events


def run_seeder() -> None:
    """Reset the release_events table and populate it with fresh sample data."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        events = generate_seed_data()
        db.add_all(events)
        db.commit()
        print(
            f"Seeded {len(events)} release events "
            f"across {len(SERVICES)} services and {len(OUTCOME_WEIGHTS)} statuses."
        )
    finally:
        db.close()


if __name__ == "__main__":
    run_seeder()
