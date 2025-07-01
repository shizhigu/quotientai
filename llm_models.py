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
                temperature=1.6
            )


gemini_2_5_flash = LiteLlm(
                model="openrouter/google/gemini-2.5-flash-preview-05-20",
                api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
                temperature=0.2
            )


gemini_2_0_flash_lite = LiteLlm(
                model="openrouter/google/gemini-2.0-flash-lite-001",
                api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
                temperature=0.2
            )


gemini_2_0_flash = LiteLlm(
                model="openrouter/google/gemini-2.0-flash-001",
                api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
                temperature=0.2
            )


sonar_reasoning_pro = LiteLlm(
                model="openrouter/perplexity/sonar-reasoning-pro",
                api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
                temperature=0.0
            )


openai_o3 = LiteLlm(
                model="openrouter/openai/o3",
                api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
                temperature=0.2
            )

deepseek_r1 = LiteLlm(
                model="openrouter/deepseek/deepseek-r1-0528",
                api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
                temperature=1.6
            )