import uvicorn
import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    print("Starting SafeGate Privacy Proxy...")
    print("Dashboard will be available at: C:/Users/sumanth/Downloads/SafeGate/frontend/index.html (Open in browser)")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
