import io
import zipfile
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def create_sample_zip() -> bytes:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("app.py", "import flask\napp = flask.Flask(__name__)\n\ndef index():\n    return 'Hello'\n")
        zf.writestr("test_app.py", "def test_index():\n    assert True\n")
        zf.writestr("README.md", "# Smart Attendance System\nSample project documentation.\n")
        zf.writestr("requirements.txt", "flask==3.0.2\npytest==8.0.0\n")
    zip_buffer.seek(0)
    return zip_buffer.read()

def test_full_project_upload_and_overview():
    zip_data = create_sample_zip()
    
    # 1. Upload Project
    response = client.post(
        "/api/projects/upload",
        files={"file": ("sample_project.zip", zip_data, "application/zip")},
        data={"student_name": "Alex Chen", "course": "CS499 Final Project"},
    )
    
    assert response.status_code == 201
    upload_res = response.json()
    project_id = upload_res["project_id"]
    assert upload_res["status"] == "analyzing"
    
    # 2. Poll Status until complete
    status_res = client.get(f"/api/projects/{project_id}/analysis-status")
    assert status_res.status_code == 200
    
    # 3. Fetch Project Overview
    overview_res = client.get(f"/api/projects/{project_id}/overview")
    assert overview_res.status_code == 200
    overview = overview_res.json()
    
    assert overview["project"]["id"] == project_id
    assert overview["project"]["student_name"] == "Alex Chen"
    assert overview["summary"]["source_files"] >= 2
    assert overview["code_metrics"]["loc"] > 0
    
    # Verify evaluation scores
    eval_scores = overview["evaluation"]
    assert eval_scores["overall_score"] is not None
    assert eval_scores["technical_execution"] is not None
    assert eval_scores["documentation_integrity"] is not None
    assert eval_scores["originality"] is not None
    
    # Verify strengths & improvements are returned
    assert isinstance(overview["strengths"], list)
    assert isinstance(overview["improvements"], list)

def test_corrupt_zip_upload_and_status():
    corrupt_data = b"NOT_A_VALID_ZIP_ARCHIVE_DATA"
    
    # 1. Upload Corrupt ZIP
    response = client.post(
        "/api/projects/upload",
        files={"file": ("corrupt.zip", corrupt_data, "application/zip")},
        data={"student_name": "Test Student", "course": "CS101"},
    )
    assert response.status_code == 201
    project_id = response.json()["project_id"]

    # 2. Check Analysis Status -> Should be failed with error message
    status_res = client.get(f"/api/projects/{project_id}/analysis-status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "failed"
    assert status_data["error"] is not None
    assert "zip" in status_data["error"].lower()

def test_reanalysis_flow():
    zip_data = create_sample_zip()
    
    # 1. Initial Upload
    response = client.post(
        "/api/projects/upload",
        files={"file": ("valid.zip", zip_data, "application/zip")},
        data={"student_name": "Alex", "course": "CS499"},
    )
    project_id = response.json()["project_id"]

    # 2. Trigger Re-analysis
    reanalyze_res = client.post(f"/api/projects/{project_id}/analyze")
    assert reanalyze_res.status_code == 200
    assert reanalyze_res.json()["status"] == "analyzing"

    # 3. Check status completes
    status_res = client.get(f"/api/projects/{project_id}/analysis-status")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "completed"

from unittest.mock import patch

def test_submit_repository_invalid_url():
    res = client.post(
        "/api/projects/repository",
        json={"git_url": "invalid-url", "student_name": "Alex", "course": "CS499"}
    )
    assert res.status_code == 400
    assert "supported" in res.json()["detail"].lower()

def test_submit_repository_valid_url():
    with patch("app.api.projects.run_analysis_background_task"):
        res = client.post(
            "/api/projects/repository",
            json={"git_url": "https://github.com/example/sample-repo.git", "student_name": "Jane", "course": "CS499"}
        )
        assert res.status_code == 201
        data = res.json()
        assert data["project_name"] == "Sample Repo"
        assert data["status"] == "analyzing"



