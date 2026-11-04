import os
import io
import zipfile
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Ensure test upload and extraction directories
os.environ["UPLOAD_DIR"] = "./test_uploads"
os.environ["EXTRACTED_DIR"] = "./test_uploads/extracted"
os.environ["MAX_UPLOAD_SIZE_MB"] = "2"  # 2MB for testing size limit
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["LLM_ENABLED"] = "false"
os.environ["LLM_TIMEOUT_SECONDS"] = "2"

import app.models  # noqa: F401 - ensure all models are registered on Base
from app.database import Base, get_db
from app.main import app
from app.config import settings

# Disable live LLM network calls by default during testing suite
settings.LLM_ENABLED = False

# Test in-memory database with SQLite StaticPool
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create fresh database tables for each test function."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Test client with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def valid_zip_bytes() -> bytes:
    """Generate a clean, valid in-memory ZIP file with a sample python script."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("main.py", "print('Hello, ProjectLens evaluation!')\n")
        zf.writestr("README.md", "# Sample Project\nThis is a sample project.\n")
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def traversal_zip_bytes() -> bytes:
    """Generate a malicious ZIP file containing a directory traversal entry."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("../evil.py", "print('Exploit!')")
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def windows_traversal_zip_bytes() -> bytes:
    """Generate a malicious ZIP with Windows backslash path traversal."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("..\\..\\windows_evil.py", "print('Windows Exploit!')")
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def absolute_path_zip_bytes() -> bytes:
    """Generate a malicious ZIP with absolute path."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("/etc/passwd", "root:x:0:0:")
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def multi_tech_zip_bytes() -> bytes:
    """
    Generate a realistic student submission archive with multiple languages,
    manifests (requirements.txt, package.json), documentation, and dataset.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Python source & manifest
        zf.writestr("backend/api.py", "from fastapi import FastAPI\napp = FastAPI()\n")
        zf.writestr("backend/requirements.txt", "fastapi==0.115.0\nsqlalchemy>=2.0.0\npydantic\n")
        # Frontend TypeScript / React & manifest
        zf.writestr("frontend/src/App.tsx", "import React from 'react';\nexport default () => <h1>Drone</h1>;\n")
        zf.writestr("frontend/src/index.ts", "console.log('App started');\n")
        zf.writestr("frontend/package.json", '{"dependencies": {"react": "^18.2.0", "tailwindcss": "^3.4.0"}}\n')
        # Java source
        zf.writestr("services/Worker.java", "public class Worker { public static void main(String[] args) {} }\n")
        # Documentation
        zf.writestr("README.md", "# Autonomous Drone\nFull stack project.\n")
        zf.writestr("docs/SRS.pdf", "%PDF-1.4 dummy pdf content")
        # Dataset
        zf.writestr("data/telemetry.csv", "timestamp,altitude,velocity\n1,100,12\n2,110,14\n")
        # Configuration
        zf.writestr("docker-compose.yml", "version: '3'\nservices:\n  web:\n    image: drone\n")
        # Git metadata indicator
        zf.writestr(".git/config", "[core]\n\trepositoryformatversion = 0\n")
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def symlink_zip_bytes() -> bytes:
    """Generate a zip with a symlink entry (POSIX 0o120000)."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zi = zipfile.ZipInfo("symlink_entry")
        zi.create_system = 3  # Unix
        zi.external_attr = 0o120777 << 16  # Symlink mode
        zf.writestr(zi, "../target")
        zf.writestr("safe.py", "print('safe')")
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def complex_python_zip_bytes() -> bytes:
    """Generate a ZIP with diverse Python structures (classes, docstrings, high CC, nesting)."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        code_main = '''"""Main module docstring."""
import os
import sys

class FlightEngine:
    """Represents a drone flight control engine."""
    def __init__(self, mode: str):
        self.mode = mode

    def calculate_thrust(self, alt: int) -> float:
        """Calculate required thrust based on altitude."""
        if alt > 1000:
            return 9.8 * 1.5
        return 9.8

def complex_decision(a, b, c, d, e):
    """Function with high cyclomatic complexity and deep nesting."""
    val = 0
    if a > 0:
        if b > 1:
            if c > 2:
                if d > 3:
                    if e > 4:
                        val = 99
                    else:
                        val = 50
                elif d == 2:
                    val = 20
            elif c == 1:
                val = 10
        elif b == 0:
            val = 5
    elif a < -10:
        for i in range(10):
            if i % 2 == 0:
                val += i
            else:
                val -= i
    else:
        while a < 0:
            a += 1
            if a == -5:
                break
    return val

# End of file comment
'''
        zf.writestr("engine/main.py", code_main)
        zf.writestr("README.md", "# Drone Telemetry Engine\nDocumentation here.\n")
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def syntax_error_python_zip_bytes() -> bytes:
    """Generate a ZIP containing one syntax error file and one valid file."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("broken.py", "def broken_syntax(:\n    return 42\n")
        zf.writestr("clean.py", "def clean_func():\n    return 'clean'\n")
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def similarity_project_a_zip() -> bytes:
    """Generate a ZIP containing standard algorithm implementation."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        code = '''def binary_search(arr, target):
    # Standard binary search implementation
    low = 0
    high = len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1
'''
        zf.writestr("algo.py", code)
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def similarity_project_b_renamed_zip() -> bytes:
    """Generate a ZIP containing the same algorithm with renamed vars and formatting."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        code = '''def binary_search(elements, value):
    # Altered comment text
    left_idx = 0
    right_idx = len(elements) - 1
    while left_idx <= right_idx:
        center = (left_idx + right_idx) // 2
        if elements[center] == value:
            return center
        elif elements[center] < value:
            left_idx = center + 1
        else:
            right_idx = center - 1
    return -1
'''
        zf.writestr("algo.py", code)
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def similarity_project_c_distinct_zip() -> bytes:
    """Generate a ZIP containing a completely different algorithm."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        code = '''class GraphBFS:
    def __init__(self):
        self.adj = {}

    def add_edge(self, u, v):
        if u not in self.adj:
            self.adj[u] = []
        self.adj[u].append(v)

    def bfs(self, start):
        visited = set([start])
        queue = [start]
        order = []
        while queue:
            node = queue.pop(0)
            order.append(node)
            for neighbor in self.adj.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return order
'''
        zf.writestr("graph.py", code)
    buffer.seek(0)
    return buffer.getvalue()

