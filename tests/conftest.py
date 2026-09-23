import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


os.environ["APP_API_KEY"] = "test-api-key"
os.environ["WEBHOOK_SECRET"] = "test-webhook-secret"

from app.database import Base, get_db
from app.main import app


TEST_DATABASE_URL = "sqlite:///./test_incidents.db"


test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False
    }
)


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[
    get_db
] = override_get_db


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(
        bind=test_engine
    )

    Base.metadata.create_all(
        bind=test_engine
    )

    yield

    Base.metadata.drop_all(
        bind=test_engine
    )


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers():
    return {
        "X-API-Key": "test-api-key"
    }


@pytest.fixture
def webhook_headers():
    return {
        "X-Webhook-Secret":
            "test-webhook-secret"
    }
