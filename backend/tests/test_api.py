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
    
    # Verify evaluation scores are explicitly null (Pending)
    eval_scores = overview["evaluation"]
    assert eval_scores["overall_score"] is None
    assert eval_scores["technical_execution"] is None
    assert eval_scores["originality"] is None
    assert eval_scores["documentation_integrity"] is None
    assert eval_scores["development_process"] is None
    
    # Verify strengths & improvements are returned
    assert isinstance(overview["strengths"], list)
    assert isinstance(overview["improvements"], list)
