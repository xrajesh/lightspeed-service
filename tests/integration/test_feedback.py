"""Integration tests for REST API endpoints for providing user feedback."""

import os

import requests
from fastapi.testclient import TestClient

# config file path needs to be set before importing app which tries to load the config
os.environ["OLS_CONFIG_FILE"] = "tests/config/valid_config.yaml"
from ols.app.main import app  # noqa: E402

client = TestClient(app)


def test_feedback() -> None:
    """Check if feedback with correct format is accepted by the service."""
    # TODO: should we validate that the correct log messages are written?
    response = client.post(
        "/v1/feedback", json={"conversation_id": 1234, "feedback_object": "blah"}
    )
    assert response.status_code == requests.codes.ok
    assert response.json() == {"status": "feedback received"}


def test_feedback_wrong_request() -> None:
    """Check if feedback with wrong payload (empty one) is not accepted by the service."""
    response = client.post("/v1/feedback", json={})
    # for the request send w/o proper payload, the server
    # should respond with proper error code
    assert response.status_code == requests.codes.unprocessable_entity


def test_feedback_wrong_not_filled_in_request() -> None:
    """Check if feedback without feedback object is not accepted by the service."""
    response = client.post(
        "/v1/feedback", json={"conversation_id": 0, "feedback_object": None}
    )
    # for the request send w/o proper payload, the server
    # should respond with proper error code
    assert response.status_code == requests.codes.unprocessable_entity
