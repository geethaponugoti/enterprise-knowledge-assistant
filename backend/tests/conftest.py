import pytest

from app import db


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test_app.db"
    monkeypatch.setattr(db, "DB_PATH", test_db_path)
    db.init_db()
    return test_db_path
