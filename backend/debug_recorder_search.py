import asyncio
import sys
from pathlib import Path

# Add mcp_servers path for imports
sys.path.insert(0, str(Path(__file__).parent / "mcp_servers" / "recorder"))
from session import RecorderSession

async def main():
    print("Initializing Recorder Session...")
    session = RecorderSession()
    
    # Force manual to ensure we can see what's happening if needed, 
    # but try headless first if cookies exist
    await session.initialize(force_manual=False)
    
    seq_num = "20141500382"
    print(f"\n--- Testing Sequence Search: {seq_num} ---")
    results = await session.search_by_sequence(seq_num)
    
    if results:
        print(f"Found {len(results)} results:")
        for r in results:
            print(r)
    else:
        print("No results found.")

    # Also test name search as fallback
    name = "LAVALLEE MADELEINE"
    print(f"\n--- Testing Name Search: {name} ---")
    results = await session.search_by_name(name)
    
    if results:
        print(f"Found {len(results)} results:")
        for r in results:
            print(r)
    else:
        print("No results found.")

    await session.close()

if __name__ == "__main__":
    asyncio.run(main())
