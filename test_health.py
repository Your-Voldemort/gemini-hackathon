import urllib.request
import json

url = "https://legalmind-backend-677928716377.us-central1.run.app/health"
print(f"\n🧪 Testing {url}\n")

try:
    with urllib.request.urlopen(url, timeout=15) as response:
        data = json.loads(response.read().decode())
        status_code = response.status
        
        print(f"✅ Status Code: {status_code}")
        print(f"✅ Response: {json.dumps(data, indent=2)}")
        
        if status_code == 200:
            print("\n🎉 SUCCESS! Backend is deployed and working!")
            print("✅ No 403 errors - Vertex AI configuration is correct!")
        
except urllib.error.HTTPError as e:
    print(f"❌ HTTP Error {e.code}: {e.reason}")
    if e.code == 403:
        print("⚠️ Still getting 403 - deployment may not be complete")
except Exception as e:
    print(f"❌ Error: {str(e)}")

print()
