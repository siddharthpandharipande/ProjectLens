"""
test_similarity.py

Comprehensive test suite for Phase 4 Code Similarity Analysis:
- Token-based similarity with normalization and shingling
- Hierarchical AST and syntax-tree structural comparison
- Graceful semantic fallback & dynamic weight re-normalization
- Candidate generation, prefiltering, and self-comparison exclusion
- Coverage-aware project aggregation
- PostgreSQL persistence idempotency and API endpoints
"""

import io
import pytest
from fastapi.testclient import TestClient

from app.services.similarity.tokenizer import CodeTokenizer
from app.services.similarity.structural import StructuralSimilarityAnalyzer
from app.services.similarity.semantic import SemanticSimilarityService
from app.services.similarity.scoring import SimilarityScoringEngine
from app.services.similarity.candidate_generator import CandidateGenerator
from app.services.similarity.service import SimilarityService
from app.models.similarity import ProjectSimilarityAnalysis, ProjectSimilarityMatch


def test_identical_source_files_similarity():
    """Identical files should produce 100% token and structural similarity."""
    code = "def add(a, b):\n    return a + b\n"
    tok_res = CodeTokenizer.calculate_token_similarity(code, code, "python", "python")
    assert tok_res["token_similarity"] == 100.0

    struct_res = StructuralSimilarityAnalyzer.calculate_structural_similarity(code, code, "python", "python")
    assert struct_res["structural_similarity"] == 100.0
    assert struct_res["is_supported"] is True


def test_formatting_and_comment_only_changes():
    """Comment-only and whitespace changes should not impact structural or token similarity."""
    code_a = """
    # Original comments
    def calculate(x, y):
        # Add values together
        result = x + y
        return result
    """
    code_b = """
    def calculate(x,y):
        # Different comment text
        result=x+y
        return result
    # Another trailing comment here
    """
    tok_res = CodeTokenizer.calculate_token_similarity(code_a, code_b, "python", "python")
    assert tok_res["token_similarity"] >= 95.0

    struct_res = StructuralSimilarityAnalyzer.calculate_structural_similarity(code_a, code_b, "python", "python")
    # Structural AST is invariant to formatting and comment changes
    assert struct_res["structural_similarity"] == 100.0


def test_renamed_variables_preserves_hierarchical_ast():
    """Renaming variables preserves parent-child control-flow AST hierarchy."""
    code_orig = """
def binary_search(arr, target):
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
    """
    code_renamed = """
def search_in_list(dataset, search_key):
    start_pointer = 0
    end_pointer = len(dataset) - 1
    while start_pointer <= end_pointer:
        pivot = (start_pointer + end_pointer) // 2
        if dataset[pivot] == search_key:
            return pivot
        elif dataset[pivot] < search_key:
            start_pointer = pivot + 1
        else:
            end_pointer = pivot - 1
    return -1
    """
    struct_res = StructuralSimilarityAnalyzer.calculate_structural_similarity(
        code_orig, code_renamed, "python", "python"
    )
    # The control-flow hierarchy (While -> If -> Return/Assign) is structurally identical
    assert struct_res["structural_similarity"] is not None
    assert struct_res["structural_similarity"] >= 75.0


def test_different_implementations_low_similarity():
    """Distinct algorithms (e.g. math vs graph traversal) yield minimal similarity."""
    code_math = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
    """
    code_graph = """
class Graph:
    def __init__(self):
        self.adj = {}
    def add_edge(self, u, v):
        self.adj.setdefault(u, []).append(v)
    def traverse(self):
        for node in self.adj:
            print(node)
    """
    tok_res = CodeTokenizer.calculate_token_similarity(code_math, code_graph, "python", "python")
    assert tok_res["token_similarity"] < 20.0

    struct_res = StructuralSimilarityAnalyzer.calculate_structural_similarity(code_math, code_graph, "python", "python")
    assert struct_res["structural_similarity"] is not None
    assert struct_res["structural_similarity"] < 25.0


def test_empty_files_similarity_is_zero():
    """Empty files must return 0.0 similarity, not a false 100% match."""
    tok_res = CodeTokenizer.calculate_token_similarity("", "", "python", "python")
    assert tok_res["token_similarity"] == 0.0

    struct_res = StructuralSimilarityAnalyzer.calculate_structural_similarity("", "", "python", "python")
    assert struct_res["structural_similarity"] == 0.0


def test_syntax_error_resiliency():
    """Syntax errors do not crash AST comparison; return None safely with error explanation."""
    broken_code = "def broken(:\n    return 1"
    valid_code = "def valid():\n    return 1"

    struct_res = StructuralSimilarityAnalyzer.calculate_structural_similarity(
        broken_code, valid_code, "python", "python"
    )
    assert struct_res["structural_similarity"] is None
    assert "syntax error" in (struct_res["error"] or "").lower()


def test_treesitter_javascript_hierarchical_comparison():
    """Tree-sitter hierarchical AST works for JavaScript code."""
    js_a = """
    class Calculator {
        add(a, b) {
            if (a > 0) {
                return a + b;
            }
            return b;
        }
    }
    """
    js_b = """
    class MathTool {
        sum(x, y) {
            if (x > 0) {
                return x + y;
            }
            return y;
        }
    }
    """
    struct_res = StructuralSimilarityAnalyzer.calculate_structural_similarity(
        js_a, js_b, "javascript", "javascript"
    )
    assert struct_res["is_supported"] is True
    assert struct_res["structural_similarity"] is not None
    assert struct_res["structural_similarity"] >= 70.0


def test_unsupported_language_ast():
    """Languages without AST parsers report is_supported=False without fabricating numbers."""
    code = "fn main() { println!(\"Hello\"); }"
    struct_res = StructuralSimilarityAnalyzer.calculate_structural_similarity(
        code, code, "rust", "rust"
    )
    assert struct_res["is_supported"] is False
    assert struct_res["structural_similarity"] is None


def test_cosine_similarity_calculation():
    """Tests mathematical correctness of vector cosine similarity."""
    v1 = [1.0, 2.0, 3.0]
    v2 = [1.0, 2.0, 3.0]
    assert abs(SemanticSimilarityService.cosine_similarity(v1, v2) - 1.0) < 1e-5

    v3 = [1.0, 0.0]
    v4 = [0.0, 1.0]
    assert abs(SemanticSimilarityService.cosine_similarity(v3, v4) - 0.0) < 1e-5

    # Zero vector returns 0.0 without division by zero
    assert SemanticSimilarityService.cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_dynamic_weight_renormalization():
    """Tests dynamic weight re-normalization when semantic or structural similarity is unavailable."""
    # When semantic is None: weights should re-normalize across token (0.30) and structural (0.40)
    score, method = SimilarityScoringEngine.calculate_file_combined_score(
        token_sim=80.0, structural_sim=90.0, semantic_sim=None
    )
    # Expected: 80 * (0.3/0.7) + 90 * (0.4/0.7) = 34.28 + 51.42 = 85.7
    assert score is not None
    assert abs(score - 85.7) <= 0.1
    assert "semantic" not in method
    assert "token" in method and "structural" in method

    # When all components are None: returns None
    score_empty, method_empty = SimilarityScoringEngine.calculate_file_combined_score(
        token_sim=None, structural_sim=None, semantic_sim=None
    )
    assert score_empty is None
    assert method_empty == "insufficient_evidence"


def test_coverage_aware_project_aggregation():
    """Tests that a tiny matching file in a large project does not dominate overall similarity."""
    # Project A has 1000 lines, Project B has 1000 lines.
    # Only one file of 10 lines matches at 100%.
    file_matches = [{
        "similarityPercent": 100.0,
        "tokenSimilarity": 100.0,
        "structuralSimilarity": 100.0,
        "semanticSimilarity": None,
        "currentSloc": 10,
        "matchedSloc": 10,
        "identicalStatements": 10,
    }]
    agg = SimilarityScoringEngine.aggregate_project_similarity(
        current_project_sloc=1000,
        matched_project_sloc=1000,
        file_matches=file_matches,
    )
    # 10 lines out of 1000 lines should be ~1.0% overall similarity, classified as minimal
    assert agg["overall_similarity"] <= 2.0
    assert agg["similarity_category"] == "minimal"
    assert agg["source_coverage_pct"] == 1.0


def test_no_eligible_cohort_projects_honest_empty(client: TestClient, similarity_project_a_zip: bytes):
    """When only 1 project exists in the DB, similarity returns an honest empty comparison."""
    # Upload single project
    resp_upload = client.post(
        "/api/projects/upload",
        files={"file": ("project_alpha.zip", similarity_project_a_zip, "application/zip")},
        data={"title": "Project Alpha", "course": "CS401"},
    )
    assert resp_upload.status_code == 201
    proj_id = resp_upload.json()["projectId"]

    # Run similarity analysis
    resp_analyze = client.post(f"/api/projects/{proj_id}/analyze/similarity")
    assert resp_analyze.status_code == 200
    data = resp_analyze.json()

    assert data["status"] == "no_candidates"
    assert data["comparedProjectsCount"] == 0
    assert data["overallSimilarity"] == 0.0
    assert len(data["matches"]) == 0


def test_multiple_projects_similarity_and_no_self_comparison(
    client: TestClient,
    similarity_project_a_zip: bytes,
    similarity_project_b_renamed_zip: bytes,
    similarity_project_c_distinct_zip: bytes,
):
    """
    Upload 3 distinct projects:
    - Project Alpha: Binary search
    - Project Beta: Binary search (renamed vars)
    - Project Gamma: Graph BFS (different)
    Verify:
    1. Alpha compares against Beta and Gamma (never itself).
    2. Beta shows high/moderate similarity to Alpha.
    3. Gamma shows minimal similarity to Alpha.
    """
    # Upload Project Alpha
    r_a = client.post(
        "/api/projects/upload",
        files={"file": ("alpha.zip", similarity_project_a_zip, "application/zip")},
        data={"title": "Project Alpha"},
    )
    proj_a = r_a.json()["projectId"]

    # Upload Project Beta
    r_b = client.post(
        "/api/projects/upload",
        files={"file": ("beta.zip", similarity_project_b_renamed_zip, "application/zip")},
        data={"title": "Project Beta"},
    )
    proj_b = r_b.json()["projectId"]

    # Upload Project Gamma
    r_c = client.post(
        "/api/projects/upload",
        files={"file": ("gamma.zip", similarity_project_c_distinct_zip, "application/zip")},
        data={"title": "Project Gamma"},
    )
    proj_c = r_c.json()["projectId"]

    # Run similarity analysis on Project Alpha
    r_sim = client.post(f"/api/projects/{proj_a}/analyze/similarity")
    assert r_sim.status_code == 200
    sim_data = r_sim.json()

    assert sim_data["status"] == "completed"
    assert sim_data["comparedProjectsCount"] == 2
    matched_ids = [m["matchedProjectId"] for m in sim_data["matches"]]

    # Verify self-comparison was excluded
    assert proj_a not in matched_ids
    assert proj_b in matched_ids
    assert proj_c in matched_ids

    # Beta should be the strongest match due to binary search structure
    beta_match = next(m for m in sim_data["matches"] if m["matchedProjectId"] == proj_b)
    gamma_match = next(m for m in sim_data["matches"] if m["matchedProjectId"] == proj_c)

    assert beta_match["overallSimilarity"] > gamma_match["overallSimilarity"]
    assert beta_match["structuralSimilarity"] is not None
    assert beta_match["structuralSimilarity"] >= 65.0
    assert len(beta_match["strongestFileMatches"]) > 0


def test_reanalysis_idempotency_no_duplicate_records(
    client: TestClient,
    similarity_project_a_zip: bytes,
    similarity_project_b_renamed_zip: bytes,
    db_session,
):
    """Running similarity analysis repeatedly updates records without duplicating rows."""
    r_a = client.post(
        "/api/projects/upload",
        files={"file": ("alpha.zip", similarity_project_a_zip, "application/zip")},
    )
    proj_a = r_a.json()["projectId"]

    client.post(
        "/api/projects/upload",
        files={"file": ("beta.zip", similarity_project_b_renamed_zip, "application/zip")},
    )

    # First analysis run
    r1 = client.post(f"/api/projects/{proj_a}/analyze/similarity")
    assert r1.status_code == 200

    count_analysis_1 = db_session.query(ProjectSimilarityAnalysis).filter_by(project_id=proj_a).count()
    count_matches_1 = db_session.query(ProjectSimilarityMatch).filter_by(project_id=proj_a).count()
    assert count_analysis_1 == 1

    # Second analysis run (re-analysis)
    r2 = client.post(f"/api/projects/{proj_a}/analyze/similarity")
    assert r2.status_code == 200

    count_analysis_2 = db_session.query(ProjectSimilarityAnalysis).filter_by(project_id=proj_a).count()
    count_matches_2 = db_session.query(ProjectSimilarityMatch).filter_by(project_id=proj_a).count()

    # Must remain exactly 1 analysis record and match rows must not duplicate
    assert count_analysis_2 == 1
    assert count_matches_2 == count_matches_1


def test_get_similarity_endpoint(
    client: TestClient,
    similarity_project_a_zip: bytes,
    similarity_project_b_renamed_zip: bytes,
):
    """GET /api/projects/{id}/similarity returns persisted analysis."""
    r_a = client.post(
        "/api/projects/upload",
        files={"file": ("alpha.zip", similarity_project_a_zip, "application/zip")},
    )
    proj_a = r_a.json()["projectId"]

    client.post(
        "/api/projects/upload",
        files={"file": ("beta.zip", similarity_project_b_renamed_zip, "application/zip")},
    )

    # Before running analysis: GET returns not_started state
    r_before = client.get(f"/api/projects/{proj_a}/similarity")
    assert r_before.status_code == 200
    assert r_before.json()["status"] == "not_started"

    # Run analysis
    client.post(f"/api/projects/{proj_a}/analyze/similarity")

    # After running analysis: GET returns saved results
    r_after = client.get(f"/api/projects/{proj_a}/similarity")
    assert r_after.status_code == 200
    data = r_after.json()
    assert data["status"] == "completed"
    assert data["comparedProjectsCount"] == 1
    assert len(data["matches"]) == 1


def test_similarity_nonexistent_project_404(client: TestClient):
    """Querying similarity for nonexistent project ID returns 404."""
    resp = client.get("/api/projects/proj_nonexistent_xyz/similarity")
    assert resp.status_code == 404

    resp_post = client.post("/api/projects/proj_nonexistent_xyz/analyze/similarity")
    assert resp_post.status_code == 404


def test_project_analysis_bundle_includes_similarity(
    client: TestClient,
    similarity_project_a_zip: bytes,
    similarity_project_b_renamed_zip: bytes,
):
    """GET /api/projects/{id}/analysis includes similarity section when completed."""
    r_a = client.post(
        "/api/projects/upload",
        files={"file": ("alpha.zip", similarity_project_a_zip, "application/zip")},
    )
    proj_a = r_a.json()["projectId"]

    client.post(
        "/api/projects/upload",
        files={"file": ("beta.zip", similarity_project_b_renamed_zip, "application/zip")},
    )

    # Run similarity analysis
    client.post(f"/api/projects/{proj_a}/analyze/similarity")

    # Fetch bundle
    resp = client.get(f"/api/projects/{proj_a}/analysis")
    assert resp.status_code == 200
    bundle = resp.json()

    modules = {m["name"]: m["status"] for m in bundle["modules"]}
    assert modules["Similarity"] == "completed"
    assert bundle["similarity"] is not None
    assert "overallSimilarity" in bundle["similarity"]
    assert "matches" in bundle["similarity"]
