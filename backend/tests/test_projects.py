import io
from fastapi.testclient import TestClient


def test_list_projects_empty(client: TestClient):
    """Test project listing with an empty database."""
    response = client.get("/api/projects")
    assert response.status_code == 200
    data = response.json()
    assert "projects" in data
    assert len(data["projects"]) == 0
    assert "stats" in data
    assert data["stats"]["totalProjects"] == 0
    assert data["stats"]["completedProjects"] == 0


def test_successful_zip_upload(client: TestClient, valid_zip_bytes: bytes):
    """Test uploading a valid ZIP archive with metadata."""
    files = {
        "file": ("submission.zip", io.BytesIO(valid_zip_bytes), "application/zip"),
    }
    data = {
        "course": "CS-402",
        "title": "Autonomous Drone Navigation",
    }
    response = client.post("/api/projects/upload", files=files, data=data)
    assert response.status_code == 201
    res_data = response.json()
    assert "projectId" in res_data
    assert res_data["projectId"].startswith("proj_")
    assert res_data["status"] == "pending"

    # Verify project appears in listing
    list_response = client.get("/api/projects")
    assert list_response.status_code == 200
    projects = list_response.json()["projects"]
    assert len(projects) == 1
    assert projects[0]["id"] == res_data["projectId"]
    assert projects[0]["title"] == "Autonomous Drone Navigation"
    assert projects[0]["course"] == "CS-402"
    assert projects[0]["status"] == "pending"


def test_upload_unsupported_file_type(client: TestClient):
    """Test rejecting non-zip files."""
    files = {
        "file": ("script.py", io.BytesIO(b"print('hello')"), "text/x-python"),
    }
    response = client.post("/api/projects/upload", files=files)
    assert response.status_code == 400
    assert "Only .zip archives are supported" in response.json()["detail"]


def test_upload_invalid_corrupt_zip(client: TestClient):
    """Test rejecting files with .zip extension that are not valid zip archives."""
    files = {
        "file": ("fake.zip", io.BytesIO(b"This is completely corrupt content not a zip!"), "application/zip"),
    }
    response = client.post("/api/projects/upload", files=files)
    assert response.status_code == 400
    assert "Corrupt or invalid ZIP archive" in response.json()["detail"]


def test_upload_path_traversal_zip(client: TestClient, traversal_zip_bytes: bytes):
    """Test rejecting zip archives containing path traversal exploits."""
    files = {
        "file": ("exploit.zip", io.BytesIO(traversal_zip_bytes), "application/zip"),
    }
    response = client.post("/api/projects/upload", files=files)
    assert response.status_code == 400
    assert "unsafe relative path traversal" in response.json()["detail"]


def test_upload_size_limit_exceeded(client: TestClient):
    """Test rejecting files that exceed MAX_UPLOAD_SIZE_MB (set to 2MB in test config)."""
    # 2.5 MB of dummy data
    large_content = b"x" * (int(2.5 * 1024 * 1024))
    files = {
        "file": ("oversized.zip", io.BytesIO(large_content), "application/zip"),
    }
    response = client.post("/api/projects/upload", files=files)
    assert response.status_code == 413
    assert "exceeds maximum allowed limit" in response.json()["detail"]


def test_get_existing_project(client: TestClient, valid_zip_bytes: bytes):
    """Test retrieving details of an existing project."""
    files = {
        "file": ("project.zip", io.BytesIO(valid_zip_bytes), "application/zip"),
    }
    upload_res = client.post("/api/projects/upload", files=files, data={"title": "Test Project"})
    project_id = upload_res.json()["projectId"]

    # Fetch project
    get_res = client.get(f"/api/projects/{project_id}")
    assert get_res.status_code == 200
    project = get_res.json()
    assert project["id"] == project_id
    assert project["title"] == "Test Project"
    assert project["status"] == "pending"
    assert "createdAt" in project
    assert "updatedAt" in project


def test_get_nonexistent_project(client: TestClient):
    """Test requesting a project ID that does not exist."""
    response = client.get("/api/projects/proj_nonexistent_123")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
