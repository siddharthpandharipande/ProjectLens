# Run ProjectLens Backend using the dedicated virtual environment
& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001

