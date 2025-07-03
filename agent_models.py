from llm_models import *

brand_intelligence_agent_model = sonar_reasoning_pro
creator_value_assessment_agent_model = gemini_2_5_flash
pricing_strategy_agent_model = sonar_reasoning_pro
negotiation_intelligence_agent_model = gemini_2_5_pro
proposal_email_agent_model = LiteLlm(
                model="openrouter/google/gemini-2.5-flash",
                api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
                temperature=0.6
            )
email_finder_agent_model = gemini_2_0_flash_lite
format_output_agent_model = gemini_2_0_flash_lite

chat_agent_model = LiteLlm(
                model="openrouter/google/gemini-2.5-flash",
                api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
                temperature=1.4
            )