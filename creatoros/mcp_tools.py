from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters, StdioConnectionParams
from google.adk.tools.langchain_tool import LangchainTool
from langchain_community.tools import TavilySearchResults
from dotenv import load_dotenv
load_dotenv()
import os

perplexity_mcp_tools = MCPToolset(
    connection_params=StdioConnectionParams(
        timeout=60,
        server_params=StdioServerParameters(
            env={   
                "PERPLEXITY_API_KEY": os.getenv("PERPLEXITY_API_KEY"),
                "PERPLEXITY_MODEL": "sonar-reasoning-pro"
            },
            command="uvx",
            args=["perplexity-mcp"],
        )
    )
)


# Instantiate the LangChain tool

os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
tavily_tool_instance = TavilySearchResults(
    max_results=3,
    search_depth="advanced",
    include_answer=True,
    include_raw_content=False,
    include_images=False,
)

# Wrap it with LangchainTool for ADK
adk_tavily_tool = LangchainTool(tool=tavily_tool_instance)


