import asyncio
import sys
from app.extensions.mqdd import workflow

async def main():
    print("Starting MQDD Workflow Test...")
    prompt = "Find an inhibitor for BRAF V600E"
    
    async for chunk in workflow.run_full_workflow(prompt):
        print(chunk, end="")
        sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())
