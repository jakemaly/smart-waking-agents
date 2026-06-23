import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI-Compatible Provider Config
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini").strip()

# API authentication key (optional but recommended for webhooks/prompts security)
API_KEY = os.getenv("API_KEY", "").strip()

# Server Settings
HOST = os.getenv("HOST", "0.0.0.0").strip()
PORT = int(os.getenv("PORT", "8000"))

# Check if OpenAI is configured or if we should run in mock mode
# We run in mock mode if OPENAI_API_KEY is empty (so the user gets a working skeleton out-of-the-box).
IS_MOCK_MODE = not OPENAI_API_KEY or OPENAI_API_KEY.lower().startswith("your-api-key")

def print_config():
    print("--- Orchestrator Configuration ---")
    print(f"OPENAI_API_BASE: {OPENAI_API_BASE}")
    print(f"OPENAI_API_KEY: {'[PRESENT]' if OPENAI_API_KEY else '[MISSING]'}")
    print(f"OPENAI_MODEL_NAME: {OPENAI_MODEL_NAME}")
    print(f"API_KEY Security: {'Enabled' if API_KEY else 'Disabled'}")
    print(f"Running Mode: {'MOCK/SIMULATED LLM' if IS_MOCK_MODE else 'REAL LLM'}")
    print(f"Server Host/Port: {HOST}:{PORT}")
    print("----------------------------------")
