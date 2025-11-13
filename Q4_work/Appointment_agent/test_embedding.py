import pandas as pd
from agents import OpenAIChatCompletionsModel, AsyncOpenAI
from pinecone import Pinecone, ServerlessSpec
import os
import glob
from dotenv import load_dotenv
import json
import openai

load_dotenv()

# Gemini API key - use synchronous client for embeddings
external_client = openai.OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/"
)

# Pinecone API key
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Test with a single text
test_text = "This is a test for medical information about fever and headache"

print("Testing embedding creation...")
try:
    response = external_client.embeddings.create(
        model="text-embedding-004",
        input=test_text
    )
    print(f"[OK] Embedding created successfully. Dimension: {len(response.data[0].embedding)}")
except Exception as e:
    print(f"[ERROR] Embedding creation failed: {e}")

# Test different model names if needed
models_to_test = [
    "text-embedding-004",
    "embedding-001",
    "embedding-gecko-001",
    "text-embedding-ada-002"
]

for model in models_to_test:
    print(f"\nTesting model: {model}")
    try:
        response = external_client.embeddings.create(
            model=model,
            input=test_text
        )
        print(f"[OK] Model {model} works. Dimension: {len(response.data[0].embedding)}")
        break
    except Exception as e:
        print(f"[ERROR] Model {model} failed: {e}")