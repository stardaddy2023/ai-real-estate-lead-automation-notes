import sys
import asyncio
import uvicorn
import os

# Force the correct event loop policy for Windows + Playwright
if sys.platform == "win32":
    # This is required for Playwright to work with asyncio on Windows
    # It must be set before any asyncio loop is created
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

if __name__ == "__main__":
    print("Starting ARELA Backend with WindowsProactorEventLoopPolicy...")
    # Run uvicorn programmatically
    # Note: reload=True might spawn subprocesses. 
    # If those subprocesses don't inherit the policy, we might need to rely on app/main.py fix as well.
    uvicorn.run(
        "app.main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=False, # Disable reload to avoid subprocess issues with Proactor loop
        loop="asyncio" # Force uvicorn to use the standard asyncio loop (which we configured)
    )
