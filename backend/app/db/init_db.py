from sqlalchemy import inspect, text
from app.db.database import engine, Base
import app.models  # Ensure all models are imported before creating tables

def init_db():
    Base.metadata.create_all(bind=engine)
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            if "project_files" in inspector.get_table_names():
                columns = [c["name"] for c in inspector.get_columns("project_files")]
                if "content" not in columns:
                    conn.execute(text("ALTER TABLE project_files ADD COLUMN content TEXT;"))
                    conn.commit()
            if "code_metrics" in inspector.get_table_names():
                cm_cols = [c["name"] for c in inspector.get_columns("code_metrics")]
                if "git_history_data" not in cm_cols:
                    conn.execute(text("ALTER TABLE code_metrics ADD COLUMN git_history_data TEXT;"))
                    conn.commit()
            if "projects" in inspector.get_table_names():
                proj_cols = [c["name"] for c in inspector.get_columns("projects")]
                if "git_url" not in proj_cols:
                    conn.execute(text("ALTER TABLE projects ADD COLUMN git_url VARCHAR(500);"))
                    conn.commit()

    except Exception:
        pass

if __name__ == "__main__":
    init_db()
    print("Database tables created successfully.")

