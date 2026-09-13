from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.project_file import ProjectFile
from app.services.token_similarity import calculate_token_similarity
from app.services.ast_similarity import calculate_ast_similarity
from app.services.semantic_similarity import calculate_semantic_similarity
from app.services.similarity_fusion import fuse_similarity_scores

def compare_two_projects(db: Session, project_a_id: str, project_b_id: str) -> Dict[str, Any]:
    """
    Compares two projects source-file by source-file, returning pairwise similarity and evidence.
    """
    proj_a = db.query(Project).filter(Project.id == project_a_id).first()
    proj_b = db.query(Project).filter(Project.id == project_b_id).first()

    if not proj_a or not proj_b:
        raise ValueError("One or both projects not found for comparison.")

    files_a = db.query(ProjectFile).filter(ProjectFile.project_id == project_a_id, ProjectFile.file_type.in_(["source", "test"])).all()
    files_b = db.query(ProjectFile).filter(ProjectFile.project_id == project_b_id, ProjectFile.file_type.in_(["source", "test"])).all()

    matching_files = []
    token_scores = []
    ast_scores = []
    semantic_scores = []

    for fa in files_a:
        for fb in files_b:
            if fa.filename == fb.filename or fa.extension == fb.extension:
                content_a = fa.content or ""
                content_b = fb.content or ""

                if not content_a or not content_b:
                    continue

                ts = calculate_token_similarity(content_a, content_b, fa.language)
                asts = calculate_ast_similarity(content_a, content_b)
                sems = calculate_semantic_similarity(content_a, content_b, fa.language)

                token_scores.append(ts["score"])
                ast_scores.append(asts["score"])
                semantic_scores.append(sems["score"])

                if ts["score"] > 0.5 or asts["score"] > 0.5:
                    matching_files.append({
                        "file_a": fa.path,
                        "file_b": fb.path,
                        "token_score": ts["score"],
                        "ast_score": asts["score"],
                        "semantic_score": sems["score"]
                    })

    avg_token = float(sum(token_scores) / len(token_scores)) if token_scores else 0.0
    avg_ast = float(sum(ast_scores) / len(ast_scores)) if ast_scores else 0.0
    avg_semantic = float(sum(semantic_scores) / len(semantic_scores)) if semantic_scores else 0.0

    fusion = fuse_similarity_scores(avg_token, avg_ast, avg_semantic)

    return {
        "project_a": {
            "id": proj_a.id,
            "name": proj_a.name,
            "student_name": proj_a.student_name,
        },
        "project_b": {
            "id": proj_b.id,
            "name": proj_b.name,
            "student_name": proj_b.student_name,
        },
        "token_similarity": fusion["token_similarity"],
        "ast_similarity": fusion["ast_similarity"],
        "semantic_similarity": fusion["semantic_similarity"],
        "overall_similarity": fusion["overall_similarity"],
        "similarity_percentage": fusion["similarity_percentage"],
        "confidence": fusion["confidence"],
        "matching_files_count": len(matching_files),
        "matching_files": matching_files[:10],
    }
