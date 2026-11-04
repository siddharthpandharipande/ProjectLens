import httpx
import json

def test():
    zip_path = 'test_data/full_drone_project.zip'
    with open(zip_path, 'rb') as f:
        files = {'file': ('full_drone_project.zip', f, 'application/zip')}
        data = {
            'course': 'CS-402 (Advanced Software Engineering)',
            'title': 'Autonomous Drone Telemetry Platform'
        }
        r = httpx.post('http://127.0.0.1:8000/api/projects/upload', files=files, data=data)
        print('UPLOAD_STATUS:', r.status_code)
        print('UPLOAD_DATA:', r.json())
        project_id = r.json()['projectId']

    r_struct = httpx.get(f'http://127.0.0.1:8000/api/projects/{project_id}/structure')
    print('STRUCTURE_STATUS:', r_struct.status_code)
    print('STRUCTURE_SUMMARY:', json.dumps(r_struct.json(), indent=2))

    r_files = httpx.get(f'http://127.0.0.1:8000/api/projects/{project_id}/files')
    print('FILES_STATUS:', r_files.status_code)
    files_data = r_files.json()
    print('TOTAL_FILES:', files_data['total'])
    for item in files_data['files'][:5]:
        print(f"  * {item['relativePath']} | {item['category']} | {item['detectedLanguage']} | {item['sizeBytes']} bytes")

if __name__ == '__main__':
    test()
