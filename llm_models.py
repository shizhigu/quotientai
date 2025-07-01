from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv
import os

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL")


gemini_2_5_pro = LiteLlm(
                model="openrouter/google/gemini-2.5-pro",
                api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
                temperature=0.1
            )


gemini_2_5_flash = LiteLlm(
                model="openrouter/google/gemini-2.5-flash",
                api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
                temperature=0.1
            )


openai_o3 = LiteLlm(
                model="openrouter/openai/o3",
                api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
                temperature=0.1
            )