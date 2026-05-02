import requests
import os

def upload():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set.")
        return

    release_id = os.environ.get("RELEASE_ID")
    if not release_id:
        print("Error: RELEASE_ID environment variable not set.")
        return

    file_path = "dist/WhisperFlow.exe"

    url = f"https://uploads.github.com/repos/ebycoco/WhisperFlow/releases/{release_id}/assets?name=WhisperFlow.exe"
    
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/octet-stream"
    }
    
    with open(file_path, "rb") as f:
        response = requests.post(url, headers=headers, data=f)
        
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    upload()
