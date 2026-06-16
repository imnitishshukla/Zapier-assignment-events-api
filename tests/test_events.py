"""Integration tests for the release event endpoints."""

from tests.conftest import create_test_event, insert_fixtures


def test_empty_list(client):
    resp = client.get("/deployments")
    assert resp.status_code == 200
    assert resp.json() == []
    assert resp.headers["X-Total-Count"] == "0"


def test_list_with_seeded_events(client, session_factory):
    insert_fixtures(
        session_factory,
        [
            create_test_event(id="evt_001", service="payment-service", status="failed"),
            create_test_event(id="evt_002", service="identity-provider", status="success"),
        ],
    )
    resp = client.get("/deployments")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert resp.headers["X-Total-Count"] == "2"
    # Confirm the response matches the documented API contract.
    assert set(body[0].keys()) == {
        "id",
        "service",
        "status",
        "duration",
        "timestamp",
        "commit_sha",
    }
    # Timestamps must be UTC ISO-8601 strings ending with "Z".
    assert body[0]["timestamp"].endswith("Z")


def test_filter_by_service(client, session_factory):
    insert_fixtures(
        session_factory,
        [
            create_test_event(id="evt_001", service="payment-service"),
            create_test_event(id="evt_002", service="identity-provider"),
        ],
    )
    resp = client.get("/deployments", params={"service": "identity-provider"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["service"] == "identity-provider"


def test_filter_by_status(client, session_factory):
    insert_fixtures(
        session_factory,
        [
            create_test_event(id="evt_001", status="success"),
            create_test_event(id="evt_002", status="failed"),
            create_test_event(id="evt_003", status="failed"),
        ],
    )
    resp = client.get("/deployments", params={"status": "failed"})
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_combined_service_and_status_filter(client, session_factory):
    insert_fixtures(
        session_factory,
        [
            create_test_event(id="evt_001", service="payment-service", status="success"),
            create_test_event(id="evt_002", service="payment-service", status="failed"),
            create_test_event(id="evt_003", service="identity-provider", status="failed"),
        ],
    )
    resp = client.get(
        "/deployments", params={"service": "payment-service", "status": "failed"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["id"] == "evt_002"


def test_invalid_status_value_returns_422(client):
    resp = client.get("/deployments", params={"status": "exploded"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == 422
    assert body["error"]["status"] == "INVALID_ARGUMENT"
    assert body["error"]["details"][0]["field"] == "status"


def test_fetch_event_by_id(client, session_factory):
    insert_fixtures(
        session_factory,
        [create_test_event(id="evt_123", service="payment-service")],
    )
    resp = client.get("/deployments/evt_123")
    assert resp.status_code == 200
    assert resp.json()["id"] == "evt_123"


def test_unknown_id_returns_404_envelope(client):
    resp = client.get("/deployments/nonexistent")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == 404
    assert body["error"]["status"] == "NOT_FOUND"
    assert body["error"]["message"] == "Deployment not found"
    # Trace id must be present on every response, including errors.
    assert resp.headers.get("X-Request-ID")
