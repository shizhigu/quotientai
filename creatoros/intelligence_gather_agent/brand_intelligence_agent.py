from google.adk.agents.llm_agent import LlmAgent
from creatoros.state_keys import STATE_BRAND_INTELLIGENCE_SUMMARY, STATE_BRAND_NAME, STATE_INQUIRY_EMAIL
from creatoros.mcp_tools import perplexity_mcp_tools, adk_tavily_tool

class BrandIntelligenceAgent(LlmAgent):
    def __init__(self):
        super().__init__(
            model="gemini-2.0-flash",
            name="BrandIntelligenceAgent",
            instruction=f"""
                ## Role & Objective

                You job is to research brands using `perplexity_mcp_tools` and returns strategic insights as JSON.

                **Input:**
                - Brand name: `{{{STATE_BRAND_NAME}}}`

                ## Execution Steps

                1. **Search Strategy**: Run 3-4 targeted searches using `perplexity_mcp_tools`:
                   - `"[Brand Name] company mission target audience 2025"`
                   - `"[Brand Name] recent marketing campaigns press releases 2025"`
                   - `"[Brand Name] competitors industry analysis"`
                   - `"[Brand Name] brand voice social media strategy"`

                2. **Research Priority**: Focus on official website, recent news, social media, competitor analysis.

                3. **Output**: Return ONLY the JSON object below (no extra text).


                ## Required JSON Output Format

                ```json
                {{
                "status": "SUCCESS",
                "summary": "One-sentence brand overview",
                "brand_profile": {{
                    "mission": "Brand's official mission statement",
                    "core_products": "Main products/services",
                    "brand_voice": "Communication style",
                    "target_audience": "Primary customer demographic",
                    "pain_points_solved": "Key problems they solve",
                    "recent_activities": [
                        {{"activity": "Campaign name", "description": "Details", "platform": "Where"}}
                    ],
                    "competitors": [
                        {{"name": "Competitor", "comment": "Strategic insight"}}
                    ],
                    "creator_opportunity": {{
                        "strengths": "Why this brand is good to work with",
                        "weaknesses": "Potential challenges",
                        "opportunities": "Growth potential for creator",
                        "threats": "Risks to consider"
                    }}
                }},
                "confidence": "High/Medium/Low",
                "sources": "Key sources used"
                }}

                ## IMPORTANT: Your final output must be ONLY the JSON object. Do not include any explanatory text, comments, or conversation before or after the JSON. Any other word or sentence is not allowed, ONLY a well-formatted JSON object surrounded by proper brackets is PERMITTED. Your output should not duplicate or rehash any of the work you did in the thinking process.
            """,
            output_key=STATE_BRAND_INTELLIGENCE_SUMMARY,
            tools=[perplexity_mcp_tools]
        )

brand_intelligence_agent = BrandIntelligenceAgent()