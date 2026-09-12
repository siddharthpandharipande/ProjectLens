from app.db.database import engine, Base
import app.models  # Ensure all models are imported before creating tables

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database tables created successfully.")
