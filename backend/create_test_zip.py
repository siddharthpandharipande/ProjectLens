import zipfile
import os

def create():
    os.makedirs('test_data', exist_ok=True)
    zip_path = 'test_data/full_drone_project.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Python backend
        zf.writestr('backend/app/main.py', 'from fastapi import FastAPI\napp = FastAPI(title="Drone Telemetry API")\n@app.get("/health")\ndef health(): return {"status": "ok"}\n')
        zf.writestr('backend/app/models.py', 'from sqlalchemy import Column, Integer, String\nclass FlightLog:\n    id = Column(Integer, primary_key=True)\n')
        zf.writestr('backend/requirements.txt', 'fastapi>=0.115.0\nsqlalchemy>=2.0.0\npydantic>=2.10.0\npytest>=8.0.0\n')
        
        # React frontend
        zf.writestr('frontend/src/App.tsx', 'import React from "react";\nexport const App = () => <div>Telemetry Dashboard</div>;\n')
        zf.writestr('frontend/src/telemetry.ts', 'export interface TelemetryPoint { altitude: number; speed: number; }\n')
        zf.writestr('frontend/package.json', '{"name": "drone-ui", "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0", "tailwindcss": "^3.4.0", "vite": "^5.0.0"}}\n')
        
        # Java controller
        zf.writestr('embedded/FlightController.java', 'public class FlightController {\n    public void stabilize() { System.out.println("Gyro stabilized"); }\n}\n')
        
        # Documentation & Data
        zf.writestr('README.md', '# Autonomous Drone Navigation System\nMulti-tier telemetry and autopilot system.\n')
        zf.writestr('docs/SRS_Specification.pdf', '%PDF-1.4 Simulated SRS Document specification')
        zf.writestr('data/waypoints.csv', 'lat,lon,alt\n37.7749,-122.4194,150\n37.7750,-122.4195,160\n')
        zf.writestr('docker-compose.yml', 'version: "3.8"\nservices:\n  drone-api:\n    build: ./backend\n')
        zf.writestr('.git/HEAD', 'ref: refs/heads/main\n')

    print('Created full_drone_project.zip successfully at:', os.path.abspath(zip_path))

if __name__ == '__main__':
    create()
