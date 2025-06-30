# from creatoros.eml_extract_agent.agent import eml_extract_agent
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents import SequentialAgent
from creatoros.intelligence_gather_agent import intelligence_gather_agent
from creatoros.contract_analysis_agent import contract_analysis_agent
from creatoros.creator_value_assessment_agent import creator_value_assessment_agent
from creatoros.pricing_strategy_agent import pricing_strategy_agent
from creatoros.proposal_email_agent import proposal_email_agent
from creatoros.negotiation_intelligence_agent import negotiation_intelligence_agent
from creatoros.format_output_agent import format_output_agent
from creatoros.email_finder_agent import email_finder_agent

async def modify_state(updates: dict, tool_context):
    """
    Modify the internal state by setting one or more key-value pairs.
    Only allows modification of specific predefined keys.
    
    Args:
        updates (dict): Dictionary containing key-value pairs to update
                       Example: {"brand_name": "Nike"} or {"brand_name": "Nike", "project_title": "Summer Campaign"}
        tool_context: ADK tool context, automatically provided by the framework
    
    Returns:
        dict: Operation result information
    """
    # Define allowed keys
    ALLOWED_KEYS = ["brand_name", "project_title", "deal_deliverables", "inquiry_email"]
    
    try:
        # Validate input
        if not isinstance(updates, dict):
            return {
                "status": "error",
                "message": "Input must be a dictionary with key-value pairs",
                "example": {"brand_name": "Nike", "project_title": "Summer Campaign"}
            }
        
        if not updates:
            return {
                "status": "error",
                "message": "Updates dictionary cannot be empty",
                "allowed_keys": ALLOWED_KEYS
            }
        
        # Check if all keys are allowed
        invalid_keys = [key for key in updates.keys() if key not in ALLOWED_KEYS]
        if invalid_keys:
            return {
                "status": "error",
                "message": f"Invalid keys: {', '.join(invalid_keys)}. Only these keys can be modified: {', '.join(ALLOWED_KEYS)}",
                "allowed_keys": ALLOWED_KEYS
            }
        
        # Apply all modifications
        results = []
        for key, value in updates.items():
            old_value = tool_context.state.get(key, "未设置")
            tool_context.state[key] = value
            results.append(f"'{key}': '{old_value}' -> '{value}'")
        
        return {
            "status": "success",
            "message": f"Successfully modified {len(updates)} key(s): {', '.join(results)}",
            "modified_keys": list(updates.keys()),
            "total_count": len(updates)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to modify state: {str(e)}"
        }

modify_state_agent = LlmAgent(
    name="ModifyStateAgent",
    description="You are a master **Modify State Agent**. Your primary function is to modify the state of the system based on user requests.",
    model="gemini-2.0-flash-lite",
    instruction="""
    You are a state management specialist. Your job is to help users modify the internal state of the system.

    IMPORTANT: You can ONLY modify these 4 specific keys:
    - brand_name: The name of the brand
    - project_title: The title of the project/campaign
    - deal_deliverables: What needs to be delivered in the deal
    - inquiry_email: The original inquiry email content

    When a user asks to modify state, you should:
    1. Identify which of the 4 allowed keys they want to modify
    2. Use the modify_state tool with a dictionary containing the key-value pairs
    3. Confirm the operation was successful

    Examples:
    - User: "Set the brand name to Nike" -> Use modify_state(updates={"brand_name": "Nike"})
    - User: "Update the project title to Summer Campaign 2024" -> Use modify_state(updates={"project_title": "Summer Campaign 2024"})
    - User: "Set brand name to Nike and project title to Summer Campaign" -> Use modify_state(updates={"brand_name": "Nike", "project_title": "Summer Campaign"})
    - User: "Update brand to Apple, title to iPhone Launch, and deliverables to 5 videos" -> Use modify_state(updates={"brand_name": "Apple", "project_title": "iPhone Launch", "deal_deliverables": "5 videos"})

    The tool accepts a dictionary, so you can modify multiple keys in a single call, which is more efficient and avoids any potential race conditions.

    If a user asks to modify any other key, politely explain that you can only modify: brand_name, project_title, deal_deliverables, and inquiry_email.

    Always be clear about what you're doing and confirm successful operations.
    """,
    tools=[modify_state],
)



deal_intelligence_agent = SequentialAgent(
    name="DealIntelligenceAgent",
    sub_agents=[
        intelligence_gather_agent,
        creator_value_assessment_agent,
        pricing_strategy_agent,
        negotiation_intelligence_agent,
        proposal_email_agent,
        email_finder_agent,
        format_output_agent
    ]
)



chat_agent = LlmAgent(
    name="ChatAgent",
    model="gemini-2.0-flash-lite",
    instruction=f"""
    You answer user's question.
    """,
)


coordinator_agent = LlmAgent(
    name="CoordinatorAgent",
    model="gemini-2.5-flash",
    instruction=f"""
    You coordinate the chat agent and the deal intelligence agent.
    If the user asks to do analysis, please delegate the task to `deal_intelligence_agent`;
    Otherwise, for all other questions or tasks, please delegate the task to `chat_agent`.
    """,
    sub_agents=[
        chat_agent,
        deal_intelligence_agent,
    ]
)

root_agent = deal_intelligence_agent