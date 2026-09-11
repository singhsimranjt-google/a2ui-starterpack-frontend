import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
from google.genai import Client

c = Client(api_key="your-gemini-api-key-here")
try:
    response = c.models.generate_content(
        model='gemini-2.5-flash',
        contents='Hello'
    )
    print("Success!", response.text)
except Exception as e:
    print("Error:", repr(e))

