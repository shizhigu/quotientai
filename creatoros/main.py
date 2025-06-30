import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from google.adk.cli.fast_api import get_fast_api_app
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Dict, Any

# 导入我们的agents
from creatoros.agent import chat_agent, deal_intelligence_agent

# =================== 辅助函数 ===================



async def get_final_response(runner: Runner, user_id: str, session_id: str, message: str) -> str:
    """
    获取agent的最终响应的辅助函数
    
    Args:
        runner: ADK Runner实例
        user_id: 用户ID
        session_id: 会话ID（必须已存在）
        message: 用户消息
        
    Returns:
        str: 最终响应文本
    """
    # 构造正确的Content格式
    content = types.Content(
        role="user",
        parts=[types.Part(text=message)]
    )
    
    final_response_text = "Agent did not produce a final response."
    all_events = []
    
    # 收集所有事件，不要提前break
    try:
        print(f"🚀 Starting agent execution for user={user_id}, session={session_id}")
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        ):
            all_events.append(event)
            # print(f"📅 Event: Author={event.author}, Final={event.is_final_response()}, Content={event.content.parts[0].text[:100] if event.content and event.content.parts else 'No content'}...")
            

            # 只在收到事件时更新响应，但不要break
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response_text = event.content.parts[0].text
                elif event.actions and event.actions.escalate:
                    final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
                    print(f"⚠️ Agent escalated: {event.author}")
        
        print(f"🏁 Workflow completed. Total events: {len(all_events)}")
        return final_response_text
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise

# 获取项目根目录
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 对于VertexAiSessionService，app_name应该是Reasoning Engine格式或简单字符串
APP_NAME = "creatoros"

# 基础配置
ALLOWED_ORIGINS = ["http://localhost", "http://localhost:8080", "*"]
SERVE_WEB_INTERFACE = True

# 简化配置：统一使用SQLite存储
SESSION_DB_URL = os.getenv("SESSION_DB_URL") # "postgresql://adk_session_service_user:Fal6imEQAx2ur1u3zOW5FHhfFTpcaxsV@dpg-d1h5u7ili9vc73bcidi0-a.oregon-postgres.render.com/adk_session_service"


print(f"💾 Using SQLite database: {SESSION_DB_URL}")

# 创建ADK FastAPI应用
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    session_service_uri=SESSION_DB_URL,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
)

# 为了保持一致性，自定义endpoints也使用相同的SQLite数据库
sqlite_session_service = DatabaseSessionService(db_url=SESSION_DB_URL)

# 创建专门的Runners用于自定义endpoint - 使用统一的SQLite存储
chat_runner = Runner(
    agent=chat_agent,
    app_name=APP_NAME,
    session_service=sqlite_session_service
)

deal_runner = Runner(
    agent=deal_intelligence_agent,
    app_name=APP_NAME,
    session_service=sqlite_session_service
)

# 定义请求/响应模型
class RunnerRequest(BaseModel):
    userId: str
    sessionId: str
    message: str
    context: Optional[Dict[str, Any]] = None

class DealAnalysisRequest(BaseModel):
    userId: str
    sessionId: str
    brandName: str
    projectTitle: str
    deliverables: Optional[List[str]] = None
    youtubeProfile: str

class DealAnalysisResponse(BaseModel):
    success: bool
    dealId: str
    analysis: Dict[str, Any]
    executionTime: Optional[float] = None

class RunnerResponse(BaseModel):
    status: str
    sessionId: str
    response: str
    executionTime: Optional[float] = None

# =================== 健康检查端点 ===================

@app.get("/health")
async def health_check():
    """健康检查端点，用于容器和负载均衡器监控"""
    return {"status": "healthy", "service": "creatoros", "version": "1.0.0"}

@app.get("/")
async def root():
    """根路径重定向到健康检查"""
    return {"message": "Creator OS API is running", "docs": "/docs", "health": "/health"}

# =================== 自定义Endpoint ===================

@app.post("/custom/chat", response_model=RunnerResponse)
async def run_chat_agent(request: RunnerRequest):
    """专门运行对话agent的endpoint - 使用现有session"""
    try:
        import time
        start_time = time.time()
        
        # Chat使用现有session，如果不存在则报错
        try:
            existing_session = await chat_runner.session_service.get_session(
                app_name=APP_NAME,
                user_id=request.userId,
                session_id=request.sessionId
            )
            if not existing_session:
                raise HTTPException(status_code=404, detail=f"Session {request.sessionId} not found for user {request.userId}")
        except Exception as e:
            if "not found" in str(e).lower():
                raise HTTPException(status_code=404, detail=f"Session {request.sessionId} not found for user {request.userId}")
            raise e
        
        # 获取最终响应
        final_response_text = await get_final_response(chat_runner, request.userId, request.sessionId, request.message)
        
        execution_time = time.time() - start_time
        
        return RunnerResponse(
            status="success",
            sessionId=request.sessionId,
            response=final_response_text,
            executionTime=execution_time
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Chat failed: {type(e).__name__}: {str(e)}")

@app.post("/custom/deal-analysis", response_model=DealAnalysisResponse)
async def run_deal_intelligence_agent(request: DealAnalysisRequest):
    """专门运行deal intelligence agent的endpoint - 总是创建新session"""
    try:
        import time
        start_time = time.time()
        print(f"🔍 Request: {request}")
        
        # Deal analysis先检查session是否存在，不存在则创建
        try:
            # 先尝试获取现有session
            existing_session = await deal_runner.session_service.get_session(
                app_name=APP_NAME,
                user_id=request.userId,
                session_id=request.sessionId
            )
            
            if existing_session:
                print(f"📊 Using existing deal analysis session: {request.sessionId} for user: {request.userId}")
            else:
                # Session不存在，创建新的
                initial_state = {
                    "brand_name": request.brandName,
                    "project_title": request.projectTitle,
                    "deal_deliverables": ", ".join(request.deliverables) if request.deliverables else None,
                    "youtube_creator_profile": request.youtubeProfile,
                    "inquiry_email": "None"
                }
                
                new_session = await deal_runner.session_service.create_session(
                    app_name=APP_NAME,
                    user_id=request.userId,
                    session_id=request.sessionId,
                    state=initial_state
                )
                print(f"📊 Created new deal analysis session: {request.sessionId} for user: {request.userId}")
                print(f"📋 Initial state: {initial_state}")
                
        except Exception as e:
            print(f"⚠️ Failed to handle deal analysis session {request.sessionId}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to handle session: {str(e)}")
        
        # 使用简单的触发消息，让agent从session state中获取信息
        trigger_message = "Please run the deal analysis agent's full workflow."
        
        # 获取最终响应（agent会从session state中读取参数）
        final_response_text = await get_final_response(deal_runner, request.userId, request.sessionId, trigger_message)
        
        execution_time = time.time() - start_time
        
        # 从session state中获取格式化后的分析结果
        try:
            # 获取更新后的session以访问最新的state
            updated_session = await deal_runner.session_service.get_session(
                app_name=APP_NAME,
                user_id=request.userId,
                session_id=request.sessionId
            )
            
            if updated_session and "formatted_output" in updated_session.state:
                # 直接使用format_output_agent生成的结构化数据
                formatted_output = updated_session.state["formatted_output"]
                if isinstance(formatted_output, dict):
                    analysis_data = formatted_output
                else:
                    # 如果formatted_output不是dict，使用默认结构
                    analysis_data = {
                        "brandName": request.brandName,
                        "projectTitle": request.projectTitle,
                        "openingQuote": 5000,
                        "alignmentScore": 85,
                        "keyStrengths": ["Data retrieval failed"],
                        "negotiationTips": ["Please retry analysis"],
                        "emailTemplate": "Data retrieval failed, please retry",
                        "suggestedEmails": []
                    }
            else:
                # 如果没有找到formatted_output，使用默认结构
                analysis_data = {
                    "brandName": request.brandName,
                    "projectTitle": request.projectTitle,
                    "openingQuote": 5000,
                    "alignmentScore": 85,
                    "keyStrengths": ["Analysis incomplete"],
                    "negotiationTips": ["Please retry analysis"],
                    "emailTemplate": "Analysis incomplete, please retry",
                    "suggestedEmails": []
                }
        except Exception as e:
            print(f"⚠️ Error retrieving formatted_output from session state: {e}")
            # 出错时使用默认结构
            analysis_data = {
                "brandName": request.brandName,
                "projectTitle": request.projectTitle,
                "openingQuote": 5000,
                "alignmentScore": 85,
                "keyStrengths": ["System error"],
                "negotiationTips": ["Please contact technical support"],
                "emailTemplate": "System error, please try again later",
                "suggestedEmails": []
            }
        
        return DealAnalysisResponse(
            success=True,
            dealId=request.sessionId,
            analysis=analysis_data,
            executionTime=execution_time
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Deal analysis failed: {type(e).__name__}: {str(e)}")




@app.get("/custom/session/state")
async def get_session_state(userId: str, sessionId: str):
    """获取指定session的状态，如果不存在则创建新session"""
    try:
        # 先尝试获取现有session
        try:
            session = await chat_runner.session_service.get_session(
                app_name=APP_NAME,
                user_id=userId,
                session_id=sessionId
            )
            if session:
                return {
                    "sessionId": sessionId,
                    "userId": userId,
                    "state": dict(session.state),
                    "created": False,
                    "lastUpdateTime": session.last_update_time
                }
        except Exception:
            # Session不存在，继续创建新的
            pass
        
        # 如果session不存在，创建一个新的
        new_session = await chat_runner.session_service.create_session(
            app_name=APP_NAME,
            user_id=userId,
            session_id=sessionId
        )
        
        return {
            "sessionId": new_session.id,
            "userId": new_session.user_id,
            "state": dict(new_session.state),
            "created": True,
            "lastUpdateTime": new_session.last_update_time
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get or create session: {str(e)}")

if __name__ == "__main__":
    # 使用uvicorn启动服务器，支持Render平台的PORT环境变量
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 