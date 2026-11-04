import io
import zipfile
import pytest
from fastapi.testclient import TestClient
from app.config import settings


def test_multi_tech_extraction_and_language_detection(client: TestClient, multi_tech_zip_bytes: bytes):
    """
    Test uploading a project with Python, TypeScript/JavaScript, Java,
    documentation, datasets, configuration, and manifests.
    Verify language detection and categorization.
    """
    files = {
        "file": ("full_project.zip", io.BytesIO(multi_tech_zip_bytes), "application/zip"),
    }
    data = {
        "title": "Full Stack Drone Platform",
        "course": "CS-402",
    }
    upload_res = client.post("/api/projects/upload", files=files, data=data)
    assert upload_res.status_code == 201
    project_id = upload_res.json()["projectId"]

    # 1. Test GET /api/projects/{project_id}/structure
    struct_res = client.get(f"/api/projects/{project_id}/structure")
    assert struct_res.status_code == 200
    struct = struct_res.json()

    assert struct["projectId"] == project_id
    assert struct["totalFiles"] >= 8
    assert struct["sourceFilesCount"] >= 4

    # Language detection checks
    languages = struct["languages"]
    assert "Python" in languages
    assert "TypeScript" in languages
    assert "Java" in languages

    # Framework detection checks
    framework_names = [f["name"] for f in struct["frameworks"]]
    assert "FastAPI" in framework_names
    assert "SQLAlchemy" in framework_names
    assert "React" in framework_names
    assert "Tailwind CSS" in framework_names

    # Repository signals checks
    assert struct["hasReadme"] is True
    assert struct["hasGit"] is True

    # Category checks
    categories = struct["categoriesSummary"]
    assert categories.get("Source Code", 0) >= 4
    assert categories.get("Documentation", 0) >= 2
    assert categories.get("Dataset", 0) >= 1
    assert categories.get("Configuration", 0) >= 1

    # 2. Test GET /api/projects/{project_id}/files
    files_res = client.get(f"/api/projects/{project_id}/files")
    assert files_res.status_code == 200
    files_data = files_res.json()
    assert files_data["total"] >= 8
    assert len(files_data["files"]) >= 8

    # Check relative paths and categories
    file_map = {f["relativePath"]: f for f in files_data["files"]}
    assert "backend/api.py" in file_map
    assert file_map["backend/api.py"]["category"] == "Source Code"
    assert file_map["backend/api.py"]["detectedLanguage"] == "Python"

    assert "frontend/src/App.tsx" in file_map
    assert file_map["frontend/src/App.tsx"]["category"] == "Source Code"
    assert file_map["frontend/src/App.tsx"]["detectedLanguage"] == "TypeScript"

    assert "services/Worker.java" in file_map
    assert file_map["services/Worker.java"]["category"] == "Source Code"
    assert file_map["services/Worker.java"]["detectedLanguage"] == "Java"

    assert "README.md" in file_map
    assert file_map["README.md"]["category"] == "Documentation"

    assert "docs/SRS.pdf" in file_map
    assert file_map["docs/SRS.pdf"]["category"] == "Documentation"

    assert "data/telemetry.csv" in file_map
    assert file_map["data/telemetry.csv"]["category"] == "Dataset"


def test_category_filtered_file_inventory(client: TestClient, multi_tech_zip_bytes: bytes):
    """Test filtering file inventory by category parameter."""
    files = {"file": ("project.zip", io.BytesIO(multi_tech_zip_bytes), "application/zip")}
    upload_res = client.post("/api/projects/upload", files=files)
    project_id = upload_res.json()["projectId"]

    # Filter by Source Code
    src_res = client.get(f"/api/projects/{project_id}/files?category=Source%20Code")
    assert src_res.status_code == 200
    for f in src_res.json()["files"]:
        assert f["category"] == "Source Code"

    # Filter by Documentation
    doc_res = client.get(f"/api/projects/{project_id}/files?category=Documentation")
    assert doc_res.status_code == 200
    for f in doc_res.json()["files"]:
        assert f["category"] == "Documentation"


def test_manifest_detection_java_rust_go(client: TestClient):
    """Test manifest-based framework detection for Java pom.xml, Rust Cargo.toml, and Go go.mod."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("pom.xml", "<project><dependencies><dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-web</artifactId></dependency></dependencies></project>")
        zf.writestr("Cargo.toml", '[package]\nname = "rust-app"\n[dependencies]\nactix-web = "4"\ntokio = { version = "1", features = ["full"] }\n')
        zf.writestr("go.mod", "module example.com/goapp\ngo 1.22\nrequire github.com/gin-gonic/gin v1.9.1\n")
        zf.writestr("main.rs", 'fn main() { println!("Hello Rust"); }\n')
        zf.writestr("main.go", 'package main\nimport "fmt"\nfunc main() { fmt.Println("Hello Go") }\n')

    buffer.seek(0)
    files = {"file": ("polyglot.zip", buffer, "application/zip")}
    upload_res = client.post("/api/projects/upload", files=files)
    project_id = upload_res.json()["projectId"]

    struct_res = client.get(f"/api/projects/{project_id}/structure")
    assert struct_res.status_code == 200
    frameworks = {f["name"]: f for f in struct_res.json()["frameworks"]}

    assert "Spring Boot" in frameworks
    assert "Actix Web" in frameworks
    assert "Tokio" in frameworks
    assert "Gin" in frameworks

    languages = struct_res.json()["languages"]
    assert "Rust" in languages
    assert "Go" in languages


def test_reparse_idempotency_no_duplicate_records(client: TestClient, multi_tech_zip_bytes: bytes):
    """Test that re-running parsing does not duplicate database records."""
    files = {"file": ("project.zip", io.BytesIO(multi_tech_zip_bytes), "application/zip")}
    upload_res = client.post("/api/projects/upload", files=files)
    project_id = upload_res.json()["projectId"]

    # Initial file count
    files_res1 = client.get(f"/api/projects/{project_id}/files")
    count1 = files_res1.json()["total"]

    # Trigger re-parse endpoint
    parse_res = client.post(f"/api/projects/{project_id}/parse")
    assert parse_res.status_code == 200

    # Ensure count remains exactly the same
    files_res2 = client.get(f"/api/projects/{project_id}/files")
    count2 = files_res2.json()["total"]
    assert count1 == count2


def test_windows_traversal_path_rejected(client: TestClient, windows_traversal_zip_bytes: bytes):
    """Test rejection of zip archives containing Windows-style path traversal."""
    files = {"file": ("windows_bad.zip", io.BytesIO(windows_traversal_zip_bytes), "application/zip")}
    response = client.post("/api/projects/upload", files=files)
    assert response.status_code == 400
    assert "path traversal" in response.json()["detail"].lower()


def test_absolute_path_rejected(client: TestClient, absolute_path_zip_bytes: bytes):
    """Test rejection of zip archives containing absolute path entries."""
    files = {"file": ("absolute_bad.zip", io.BytesIO(absolute_path_zip_bytes), "application/zip")}
    response = client.post("/api/projects/upload", files=files)
    assert response.status_code == 400
    assert "absolute path" in response.json()["detail"].lower()


def test_symlink_safe_handling(client: TestClient, symlink_zip_bytes: bytes):
    """Test that symbolic links in zip archives are safely skipped and not followed."""
    files = {"file": ("symlink.zip", io.BytesIO(symlink_zip_bytes), "application/zip")}
    upload_res = client.post("/api/projects/upload", files=files)
    assert upload_res.status_code == 201
    project_id = upload_res.json()["projectId"]

    # Files listing should have extracted safe.py and not created broken symlinks
    files_res = client.get(f"/api/projects/{project_id}/files")
    assert files_res.status_code == 200
    rel_paths = [f["relativePath"] for f in files_res.json()["files"]]
    assert "safe.py" in rel_paths
    assert "symlink_entry" not in rel_paths


def test_structure_nonexistent_project_404(client: TestClient):
    """Test 404 when requesting structure for unknown project ID."""
    response = client.get("/api/projects/proj_nonexistent_xyz/structure")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_files_nonexistent_project_404(client: TestClient):
    """Test 404 when requesting file inventory for unknown project ID."""
    response = client.get("/api/projects/proj_nonexistent_xyz/files")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_minimal_empty_project(client: TestClient):
    """Test minimal project with single empty file."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("empty.py", "")
    buffer.seek(0)

    files = {"file": ("minimal.zip", buffer, "application/zip")}
    res = client.post("/api/projects/upload", files=files)
    assert res.status_code == 201
    project_id = res.json()["projectId"]

    struct = client.get(f"/api/projects/{project_id}/structure").json()
    assert struct["totalFiles"] == 1
    assert struct["sourceFilesCount"] == 1
    assert "Python" in struct["languages"]
