import uvicorn
import webbrowser
import threading
import time
from config import config

def open_browser(url: str):
    time.sleep(1.5)
    print(f"\n[ScholarAI] Opening browser at {url} ...")
    try:
        webbrowser.open(url)
    except Exception:
        pass

if __name__ == "__main__":
    host = config.HOST
    port = config.PORT
    url = f"http://{host}:{port}"
    
    print("=" * 65)
    print(" [ScholarAI] Master's Scholarship Finder Agent")
    print(f" [*] Server URL: {url}")
    print(f" [*] Working Directory: C:\\Users\\SM\\.gemini\\antigravity\\scratch\\master_scholarship_agent")
    print("=" * 65)

    threading.Thread(target=open_browser, args=(url,), daemon=True).start()
    
    uvicorn.run("app:app", host=host, port=port, reload=False)
