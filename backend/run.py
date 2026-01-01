import sys
import asyncio
import uvicorn

if __name__ == "__main__":
    # Fix for Playwright on Windows: Force ProactorEventLoop
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Run uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
