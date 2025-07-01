from google.adk.agents.llm_agent import LlmAgent
from pydantic import BaseModel, Field
from typing import List, Optional

class Contact(BaseModel):
    full_name: str = Field(description="the full name of the contact person")
    position: str = Field(description="the job position/title")
    email: str = Field(description="the contact email address")
    confidence_score: int = Field(description="the confidence score of the contact information")

class FormatOutputAgentResponse(BaseModel):
    brandName: str = Field(description="the brand name")
    projectTitle: str = Field(description="the project title")
    openingQuote: int = Field(description="the opening quote price. A numeric value the creator should start the negotiation with")
    minimum_acceptable: int = Field(description="the minimum acceptable price. A numeric value the creator should not go below")
    target_quote: int = Field(description="the target quote price. A numeric value the creator should aim for")
    alignmentScore: int = Field(description="the alignment score. A numeric value between 0 and 100")
    keyStrengths: List[str] = Field(description="the key strengths")
    negotiationTips: List[str] = Field(description="the negotiation tips")
    emailTemplate: str = Field(description="the email template")
    suggestedEmails: List[Contact] = Field(description="the suggested contacts for outreach with detailed information")

format_output_agent = LlmAgent(
    name="FormatOutputAgent",
    description="A specialized agent that extracts and formats deal intelligence analysis into structured JSON output",
    model="gemini-2.5-flash-lite",
    instruction="""You are a data extraction specialist. Your ONLY task is to locate and extract specific information from the previous conversation context and format it into a precise JSON structure.

CRITICAL REQUIREMENTS:
1. You MUST output ONLY valid JSON - no additional text, explanations, or markdown formatting
2. DO NOT analyze, interpret, or generate new content
3. ONLY extract existing information from the conversation history and analysis reports in the context
4. Use the exact field names specified in the schema
5. Ensure all numeric values are actual numbers (not strings)
6. If specific information is mentioned in the previous analysis, extract it exactly as provided

REQUIRED JSON STRUCTURE:
```json
{
    "brandName": "Extract the exact brand name from session state or conversation",
    "projectTitle": "Extract the exact project title from session state or conversation", 
    "openingQuote": numeric_value_in_dollars,
    "alignmentScore": numeric_score_0_to_100,
    "minimum_acceptable": numeric_value_in_dollars,
    "target_quote": numeric_value_in_dollars
    "keyStrengths": ["extract from analysis", "extract from analysis", "extract from analysis"],
    "negotiationTips": ["extract from analysis", "extract from analysis", "extract from analysis"],
    "emailTemplate": "Extract the complete email template from previous analysis",
    "suggestedEmails": [
        {
            "full_name": "John Smith",
            "position": "Social Media Director",
            "email": "john.smith@patagonia.com",
            "confidence_score": 92
        }
    ]
}
```

EXTRACTION INSTRUCTIONS:
- brandName: Find and copy the exact brand name from context
- projectTitle: Find and copy the exact project title from context
- openingQuote: Locate the specific price recommendation from the analysis report
- alignmentScore: Find the exact alignment/compatibility score from the analysis
- keyStrengths: Extract the list of strengths/advantages mentioned in the analysis
- negotiationTips: Extract the specific negotiation recommendations from the analysis. Specifically, from the `negotiation_intelligence['general_strategy_guidelines']` array.
- emailTemplate: Copy the complete email template provided in the analysis
- suggestedEmails: Extract the contact objects from the email finder results. Look for "recommended_contacts" array and extract:
  * full_name: The person's full name
  * position: Their job title/position
  * email: The email address
  * confidence_score: The confidence score (numeric)

IMPORTANT: The previous analysis contains all this information. Your job is to FIND and EXTRACT it, not create new content. Look through the conversation history and analysis reports to locate each piece of data.

OUTPUT ONLY THE JSON OBJECT - NO OTHER TEXT OR FORMATTING.""",
    output_key="formatted_output",
    output_schema=FormatOutputAgentResponse
)
