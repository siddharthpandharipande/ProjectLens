import psycopg

def test_db():
    try:
        with psycopg.connect("host=localhost port=5432 user=postgres password=postgres dbname=postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = 'projectlens_db'")
                if not cur.fetchone():
                    cur.execute("CREATE DATABASE projectlens_db")
                    print("SUCCESS: Database projectlens_db created!")
                else:
                    print("SUCCESS: Database projectlens_db already exists!")
    except Exception as e:
        print("CONNECT_ERROR:", e)

if __name__ == "__main__":
    test_db()
