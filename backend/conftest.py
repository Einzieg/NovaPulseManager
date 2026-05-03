from pathlib import Path
from uuid import uuid4

import pytest


@pytest.fixture
def temp_db_path():
    db_dir = Path(__file__).resolve().parent.parent / "database" / ".pytest"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / f"{uuid4().hex}.db"

    yield db_path

    from database.db_session import db

    if not db.is_closed():
        db.close()
    if db_path.exists():
        db_path.unlink()
