import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
from google.genai import Client

async def test():
    c = Client()
    try:
        response = await c.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents='Hello'
        )
        print("Success!", response.text)
    except Exception as e:
        print("Error:", repr(e))

asyncio.run(test())
