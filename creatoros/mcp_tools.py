from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters, StdioConnectionParams
from google.adk.tools.langchain_tool import LangchainTool
from google.adk.tools import LongRunningFunctionTool
from langchain_community.tools import TavilySearchResults
from google.adk.tools.tool_context import ToolContext
from dotenv import load_dotenv
import os
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from creatoros.state_keys import STATE_GENERATED_PROPOSAL_EMAIL
from supabase import create_client, Client
from google.adk.agents.callback_context import CallbackContext
from google.genai.types import Content

load_dotenv()

supabase_mcp_tools = MCPToolset(
    connection_params=StdioConnectionParams(
        timeout=300,
        server_params=StdioServerParameters(
            env={   
                "SUPABASE_ACCESS_TOKEN": "sbp_a269e621935b289fbb4dd9102bfe0fb8eee66cfa",
            },
            command="npx",
            args=["-y", "@supabase/mcp-server-supabase@latest"],
        )
    )
)

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

async def email_update_after_agent_callback(callback_context: CallbackContext) -> Optional[Content]:
    """
    After agent callback that automatically updates email templates in both ADK state and Supabase database.
    
    This callback is designed to be attached to agents that generate or modify email content.
    It automatically detects if there's email content that needs to be updated and performs
    dual synchronization between ADK session state and the Supabase database.
    
    Args:
        callback_context (CallbackContext): ADK callback context automatically provided by the framework.
                                           Contains state, session info, and invocation details.
    
    Returns:
        Optional[Content]: None to preserve agent's original output, or Content to modify it.
                          This callback preserves the agent's response while performing background updates.
    
    Behavior:
        - Automatically detects if STATE_GENERATED_PROPOSAL_EMAIL exists in state
        - If found, updates both ADK state and Supabase database records
        - Logs all operations for debugging and monitoring
        - Fails gracefully without affecting agent's primary response
        - Returns None to preserve agent's original output
    
    State Updates:
        - ADK: Updates STATE_GENERATED_PROPOSAL_EMAIL in session state
        - Database: Updates latest_analysis_data.emailTemplate in Supabase 'deals' table
    
    Usage:
        ```python
        agent = LlmAgent(
            name="EmailGeneratorAgent",
            instruction="Generate email templates...",
            after_agent_callback=email_update_after_agent_callback
        )
        ```
    
    Note:
        - Requires valid SUPABASE_URL and SUPABASE_KEY environment variables
        - Session info accessed via callback_context.invocation_context.session
        - Designed to be non-intrusive - never affects agent's primary response
        - All errors are logged but don't interrupt the agent flow
    """
    
    try:
        # Step 1: Check if there's email content to update
        email_content = callback_context.state.get(STATE_GENERATED_PROPOSAL_EMAIL)
        if not email_content:
            print("DEBUG: No email content found in state, skipping update")
            return None  # No email to update, preserve original response
        
        # Validate email content
        if not isinstance(email_content, str) or len(email_content.strip()) == 0:
            print("WARNING: Invalid email content format, skipping update")
            return None
        
        print(f"INFO: Found email content ({len(email_content)} chars), proceeding with updates")
        
        # Step 2: Get session information for database update
        session = callback_context.invocation_context.session
        session_id = session.id
        profile_id = session.user_id
        
        if not session_id or not profile_id:
            print("WARNING: Missing session_id or user_id, skipping database update")
            return None
        
        print(f"INFO: Processing update for session_id: {session_id}, profile_id: {profile_id}")
        
        # Step 3: Update Supabase database
        database_update_success = False
        try:
            # Query existing record
            response = supabase.table("deals").select("*").eq("session_id", session_id).eq("profile_id", profile_id).execute()
            
            if not response.data:
                print(f"WARNING: No database record found for session_id: {session_id}, profile_id: {profile_id}")
            else:
                # Get current analysis data
                current_record = response.data[0]
                latest_analysis_data = current_record.get("latest_analysis_data", {})
                
                # Update email template in analysis data
                latest_analysis_data["emailTemplate"] = email_content
                
                # Update database record
                update_response = supabase.table("deals").update({
                    "latest_analysis_data": latest_analysis_data
                }).eq("session_id", session_id).eq("profile_id", profile_id).execute()
                
                if update_response.data:
                    database_update_success = True
                    print(f"SUCCESS: Database updated successfully for session {session_id}")
                else:
                    print("ERROR: Database update returned no data")
                    
        except Exception as db_error:
            print(f"ERROR: Database update failed: {str(db_error)}")
        
        # Step 4: Log final status
        if database_update_success:
            print(f"SUCCESS: Email callback completed - State: ✅ Database: ✅")
        else:
            print(f"PARTIAL: Email callback completed - State: ✅ Database: ❌")
        
        # Always return None to preserve the agent's original response
        return None
        
    except Exception as general_error:
        print(f"ERROR: Email update callback failed: {str(general_error)}")
        # Never interrupt the agent flow, even on errors
        return None

# perplexity_mcp_tools = MCPToolset(
#     connection_params=StdioConnectionParams(
#         timeout=300,
#         server_params=StdioServerParameters(
#             env={   
#                 "PERPLEXITY_API_KEY": os.getenv("PERPLEXITY_API_KEY"),
#                 # "PERPLEXITY_MODEL": "sonar-reasoning-pro"
#             },
#             command="npx",
#             args=["-y", "server-perplexity-ask"],
#         )
#     )
# )

# tavily_tool_instance = TavilySearchResults(
#     max_results=3,
#     search_depth="advanced",
#     include_answer=True,
#     include_raw_content=False,
#     include_images=False,
# )

# # Wrap it with LangchainTool for ADK
# adk_tavily_tool = LangchainTool(tool=tavily_tool_instance)


# Native async Perplexity search tool
async def perplexity_search(query: str) -> Dict[str, Any]:
    """
    Perform real-time search and Q&A using Perplexity API.
    
    Args:
        query (str): Search query or question
    
    Returns:
        Dict[str, Any]: Dictionary containing search results with:
            - status: Execution status
            - answer: Generated response
            - citations: List of citation links
    
    Examples:
        >>> result = await perplexity_search("What is AI?")
        >>> result = await perplexity_search("Latest tech news")
    """
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "error": "PERPLEXITY_API_KEY not found in environment variables"
        }
    
    # Hardcoded configuration
    model = "sonar-reasoning-pro" # "sonar-pro"
    # max_tokens = 800
    temperature = 0.0
    # search_domain_filter = ["wikipedia.org", "arxiv.org", "github.com"]  # Trusted sources
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "Be precise and informative. Provide accurate information with proper citations."
            },
            {
                "role": "user",
                "content": query
            }
        ],
        # "max_tokens": max_tokens,
        "temperature": temperature,
        # "search_domain_filter": search_domain_filter
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "success",
                        "answer": data["choices"][0]["message"]["content"],
                        "citations": data.get("citations", []),
                        # "usage": data.get("usage", {}),
                        # "model": data.get("model", model),
                        "query": query
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "error": f"API request failed with status {response.status}",
                        "details": error_text
                    }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Exception occurred: {str(e)}"
        }


# Native async Tavily search tool
async def tavily_search(query: str) -> Dict[str, Any]:
    """
    Perform web search using Tavily API to get real-time search results.
    
    Args:
        query (str): Search query string. The length of the query MUST be less than 400 tokens. Please keep the query concise.
    
    Returns:
        Dict[str, Any]: Dictionary containing search results with:
            - status: Execution status
            - answer: AI-generated answer
            - results: List of search results
            - query: Search query
            - response_time: Response time
    
    Examples:
        >>> result = await tavily_search("Python programming")
        >>> result = await tavily_search("AI news")
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "error": "TAVILY_API_KEY not found in environment variables"
        }
    
    # Hardcoded configuration
    search_depth = "advanced"
    max_results = 3
    include_answer = True
    include_raw_content = False
    include_images = False
    
    url = "https://api.tavily.com/search"
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": search_depth,
        "max_results": max_results,
        "include_answer": include_answer,
        "include_raw_content": include_raw_content,
        "include_images": include_images
    }
    
    try:
        start_time = asyncio.get_event_loop().time()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                end_time = asyncio.get_event_loop().time()
                response_time = round(end_time - start_time, 2)
                
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "success",
                        "answer": data.get("answer", ""),
                        "results": data.get("results", []),
                        "query": query,
                        "response_time": response_time,
                        "follow_up_questions": data.get("follow_up_questions", []),
                        "images": data.get("images", []) if include_images else []
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "error": f"API request failed with status {response.status}",
                        "details": error_text,
                        "response_time": response_time
                    }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Exception occurred: {str(e)}"
        }


perplexity_mcp_tools = LongRunningFunctionTool(perplexity_search)
adk_tavily_tool = LongRunningFunctionTool(tavily_search)


# Native async Tavily Q&A search tool
async def tavily_qna_search(query: str) -> Dict[str, Any]:
    """
    Perform Q&A search using Tavily API to get concise answers to questions.
    
    Args:
        query (str): Question query string
    
    Returns:
        Dict[str, Any]: Dictionary containing Q&A results with:
            - status: Execution status
            - answer: Concise answer
            - query: Original question
    
    Examples:
        >>> result = await tavily_qna_search("Who is the CEO of Google?")
        >>> result = await tavily_qna_search("What is the capital of France?")
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "error": "TAVILY_API_KEY not found in environment variables"
        }
    
    url = "https://api.tavily.com/search"
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": 3,
        "include_answer": True,
        "include_raw_content": False,
        "include_images": False
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    answer = data.get("answer", "")
                    
                    # If no direct answer, extract content from first result
                    if not answer and data.get("results"):
                        first_result = data["results"][0]
                        answer = first_result.get("content", "")[:200] + "..."
                    
                    return {
                        "status": "success",
                        "answer": answer,
                        "query": query
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "error": f"API request failed with status {response.status}",
                        "details": error_text
                    }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Exception occurred: {str(e)}"
        }