# test_upload.py - Run this from your LOCAL machine to test the server

import requests
import time
import sys
import os

# Server configuration
SERVER_IP = "70.187.30.25"  # Your vast.ai server IP
PORT = 8384
BASE_URL = f"http://{SERVER_IP}:{PORT}"

# Local video file path
VIDEO_PATH = r"C:\Users\Dell\Downloads\MicrosoftTeams-video.mp4"

def test_upload():
    print("=" * 60)
    print("Testing GPU Pipeline with Direct Upload")
    print("=" * 60)
    
    # Check if video exists
    if not os.path.exists(VIDEO_PATH):
        print(f"❌ Video not found: {VIDEO_PATH}")
        return
    
    file_size = os.path.getsize(VIDEO_PATH)
    print(f"📹 Video: {os.path.basename(VIDEO_PATH)}")
    print(f"📏 Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
    
    # Upload video
    print("\n📤 Uploading to GPU server...")
    
    with open(VIDEO_PATH, "rb") as f:
        files = {"video_file": (os.path.basename(VIDEO_PATH), f, "video/mp4")}
        data = {"language": "en"}
        
        try:
            response = requests.post(
                f"{BASE_URL}/test-local",
                files=files,
                data=data,
                timeout=60
            )
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to {BASE_URL}")
            print("Make sure the server is running and port 8384 is accessible")
            return
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text)
        return
    
    result = response.json()
    print(f"\n✅ Upload successful!")
    print(f"📝 Video ID: {result.get('videoId')}")
    print(f"📝 Status: {result.get('status')}")
    
    video_id = result.get('videoId')
    
    # Monitor processing
    print(f"\n⏳ Monitoring processing for {video_id}...")
    print("Press Ctrl+C to stop monitoring\n")
    
    try:
        for i in range(60):  # Monitor for 2 minutes
            time.sleep(2)
            
            status_response = requests.get(f"{BASE_URL}/test-status/{video_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                
                if status_data.get('found'):
                    print(f"\n✅ Processing complete! Found in logs:")
                    print("=" * 60)
                    print(status_data.get('logs', 'No logs found'))
                    print("=" * 60)
                    return
                else:
                    print(f"[{i*2}s] Processing... (not in logs yet)", end="\r", flush=True)
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Monitoring stopped by user")
        print(f"Check status later: curl {BASE_URL}/test-status/{video_id}")

if __name__ == "__main__":
    test_upload()