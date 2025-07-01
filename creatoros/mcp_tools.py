from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters, StdioConnectionParams
from google.adk.tools.langchain_tool import LangchainTool
from google.adk.tools import LongRunningFunctionTool
from langchain_community.tools import TavilySearchResults
from dotenv import load_dotenv
import os
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List

load_dotenv()

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
    # temperature = 0.3
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
        # "temperature": temperature,
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