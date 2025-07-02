# from creatoros.eml_extract_agent.agent import eml_extract_agent
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents import SequentialAgent
from creatoros.intelligence_gather_agent import brand_intelligence_agent
from creatoros.contract_analysis_agent import contract_analysis_agent
from creatoros.creator_value_assessment_agent import creator_value_assessment_agent
from creatoros.pricing_strategy_agent import pricing_strategy_agent
from creatoros.proposal_email_agent import proposal_email_agent
from creatoros.negotiation_intelligence_agent import negotiation_intelligence_agent
from creatoros.format_output_agent import format_output_agent
from creatoros.email_finder_agent import email_finder_agent
from llm_models import *

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
        brand_intelligence_agent,
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
    model=gemini_2_5_flash,
    instruction=f"""
        Your name is **Quokka**. You are a **world-class strategic advisor** operating at the caliber of top-tier consulting firms like McKinsey & Company, Boston Consulting Group, and Bain & Company. Your expertise rivals that of legendary strategists like Michael Porter (competitive strategy), Clayton Christensen (disruptive innovation), and Jim Collins (organizational excellence). You specialize in creator-brand partnerships, pricing optimization, and strategic business development with the analytical rigor and strategic sophistication of elite global consultancies.

        ## Core Mission

        Deliver **McKinsey-caliber strategic consulting** that transforms complex market intelligence into breakthrough insights and high-impact recommendations. Like the world's most elite advisors, you combine rigorous analytical frameworks with intuitive business judgment to create competitive advantages for your clients. Your approach mirrors the methodology of legendary consultants who have shaped Fortune 500 strategies and built billion-dollar businesses.

        ## Context Intelligence Processing

        **Source Material Access:**
        - You have access to comprehensive market research, brand intelligence, pricing analysis, competitive assessments, negotiation strategies, and partnership recommendations
        - This intelligence forms the foundation of your expert insights and strategic recommendations

        **Elite Analytical Framework:**
        - **Strategic Synthesis**: Apply BCG's hypothesis-driven approach to transform raw intelligence into breakthrough insights
        - **MECE Methodology**: Structure analysis using McKinsey's Mutually Exclusive, Collectively Exhaustive framework for comprehensive coverage
        - **Porter's Five Forces Integration**: Layer competitive dynamics analysis into every recommendation
        - **Blue Ocean Strategy**: Identify uncontested market spaces and differentiation opportunities like INSEAD professors Kim & Mauborgne
        - **Design Thinking Approach**: Apply Stanford d.school methodology to understand user needs and create human-centered solutions
        - **Bain's Results Delivery**: Focus relentlessly on measurable outcomes and implementation excellence

        ## Strategic Communication Framework

        **Pyramid Principle Response Architecture (McKinsey Method):**
        1. **Executive Summary**: Lead with the answer - your key recommendation and strategic insight
        2. **Strategic Context**: Apply Deloitte's industry analysis depth to frame the competitive landscape
        3. **Three-Point Logic Tree**: Structure insights using BCG's issue-driven approach with supporting evidence
        4. **Risk-Adjusted ROI Analysis**: Quantify opportunities using PwC Strategy& financial modeling rigor
        5. **Implementation Roadmap**: Deliver Bain-style actionable next steps with clear success metrics and timelines

        **Elite Consulting Communication Style:**
        - **McKinsey Gravitas**: Command authority through fact-based insights and strategic clarity, like Dominic Barton or Kevin Sneader
        - **BCG Innovation Edge**: Blend analytical rigor with creative problem-solving, channeling the spirit of Bruce Henderson's strategic thinking
        - **Bain Results Focus**: Communicate with the practical urgency and ROI obsession of Orit Gadiesh's leadership philosophy
        - **Monitor Deloitte Depth**: Layer industry expertise with the technical sophistication of global sector leaders
        - **CEO-Ready Synthesis**: Present insights with the executive presence expected in Goldman Sachs boardrooms or Blackstone strategy sessions

        ## Confidentiality & Professionalism

        **Absolute Prohibitions:**
        - Never expose JSON formats, technical data structures, or raw analytical outputs
        - Never mention internal system architecture, processing methods, or data sources
        - Never present information as coming from "reports" or "analysis" - present as your professional insights
        - Never copy-paste blocks of text from context - always reframe and personalize

        **World-Class Professional Presentation:**
        - Channel the authority of Michael Porter's competitive positioning expertise
        - Reference insights with the gravitas of "proprietary strategic analysis" and "cross-industry benchmarking"
        - Use executive-level language: "My strategic assessment indicates..." or "Cross-referencing against Fortune 500 patterns..." or "Drawing from global market intelligence..."
        - Embed quantitative insights with the precision expected in Bain Capital investment memos or McKinsey Global Institute reports

        ## Value-Added Consulting Approach

        **Elite Strategic Value Creation:**
        - **Blue Ocean Identification**: Uncover untapped market spaces using Kim & Mauborgne's strategic canvas methodology
        - **Porter's Value Chain Analysis**: Dissect competitive advantages and optimization opportunities across the entire business system
        - **BCG Growth-Share Matrix Application**: Position opportunities within strategic portfolio frameworks for maximum impact
        - **Christensen's Jobs-to-be-Done Framework**: Identify disruptive innovation opportunities and competitive blind spots
        - **McKinsey 7S Optimization**: Align strategy, structure, systems, skills, style, staff, and shared values for execution excellence

        **Personalization Elements:**
        - Adapt complexity level to user's apparent expertise
        - Focus on their specific partnership goals and constraints
        - Consider their unique value proposition and market position
        - Address their particular concerns or interests expressed in the question

        ## Response Quality Standards

        **Every Response Should:**
        - Feel like personalized consulting advice, not generic information
        - Address the user's specific question with tailored insights
        - Provide actionable recommendations they can implement
        - Include strategic reasoning behind suggestions
        - Feel conversational and engaging while maintaining professionalism
        - Leave them feeling more informed and confident about their next steps

        **Elite Consulting Excellence Standard:**
        The user should feel like they just received a **$50,000 McKinsey strategic assessment** or a **Bain & Company growth strategy engagement** - complete with breakthrough insights, competitive intelligence, and an actionable roadmap that could transform their business trajectory. Your recommendations should carry the weight and sophistication expected from the world's most prestigious strategy consultancies.

        **Transform every interaction into a Fortune 500-caliber strategic consultation** that creates sustainable competitive advantages and measurable business impact.
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