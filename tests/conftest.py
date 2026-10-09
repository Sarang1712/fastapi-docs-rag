import pytest
from app import db

@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_DB", str(tmp_path / "test.db"))
    db.init_db()