import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import aiohttp
import tempfile

from google.adk.cli.fast_api import get_fast_api_app
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Dict, Any

# 导入我们的agents
from creatoros.agent import chat_agent, deal_intelligence_agent

# =================== 配置常量 ===================
MAX_IMAGE_SIZE_MB = 10  # Maximum image size in MB
MAX_IMAGES_COUNT = 6    # Maximum number of images per request
TEMP_DIR = tempfile.gettempdir()  # Use system temp directory

# =================== 辅助函数 ===================

async def process_profileImages(profileImages: List[str]) -> List[types.Part]:
    """
    Process profile image URLs and convert them to Google GenAI content parts.
    
    Features:
    - Memory-efficient processing with size limits
    - Temporary file cleanup
    - Error handling and logging
    - Best practices from Google GenAI documentation
    
    Args:
        profileImages: List of image URLs
        
    Returns:
        List[types.Part]: List of image content parts
        
    Raises:
        HTTPException: If too many images or images too large
    """
    if not profileImages:
        return []
    
    # Validate input limits
    if len(profileImages) > MAX_IMAGES_COUNT:
        raise HTTPException(
            status_code=400, 
            detail=f"Too many images. Maximum {MAX_IMAGES_COUNT} images allowed."
        )
        
    print(f"🖼️ Processing {len(profileImages)} profile images...")
    image_parts = []
    temp_files = []  # Track temporary files for cleanup
    
    try:
        async with aiohttp.ClientSession() as session:
            for i, image_url in enumerate(profileImages):
                try:
                    print(f"📥 Downloading image {i+1}/{len(profileImages)}: {image_url}")
                    
                    async with session.get(image_url) as response:
                        if response.status == 200:
                            # Check content length before downloading
                            content_length = response.headers.get('content-length')
                            if content_length:
                                size_mb = int(content_length) / (1024 * 1024)
                                if size_mb > MAX_IMAGE_SIZE_MB:
                                    print(f"⚠️ Skipping image {i+1}: too large ({size_mb:.1f}MB > {MAX_IMAGE_SIZE_MB}MB)")
                                    continue
                            
                            image_data = await response.read()
                            
                            # Double-check actual size
                            actual_size_mb = len(image_data) / (1024 * 1024)
                            if actual_size_mb > MAX_IMAGE_SIZE_MB:
                                print(f"⚠️ Skipping image {i+1}: too large ({actual_size_mb:.1f}MB > {MAX_IMAGE_SIZE_MB}MB)")
                                continue
                            
                            # Get MIME type from response headers first
                            mime_type = response.headers.get('content-type', '').split(';')[0]
                            
                            # Fallback to URL extension if no content-type header
                            if not mime_type or not mime_type.startswith('image/'):
                                url_lower = image_url.lower()
                                if url_lower.endswith(('.png',)):
                                    mime_type = "image/png"
                                elif url_lower.endswith(('.jpg', '.jpeg')):
                                    mime_type = "image/jpeg"
                                elif url_lower.endswith(('.gif',)):
                                    mime_type = "image/gif"
                                elif url_lower.endswith(('.webp',)):
                                    mime_type = "image/webp"
                                else:
                                    mime_type = "image/jpeg"  # Default fallback
                            
                            # Create image part using Google GenAI best practices
                            image_part = types.Part.from_bytes(
                                data=image_data, 
                                mime_type=mime_type
                            )
                            
                            image_parts.append(image_part)
                            print(f"✅ Successfully processed image {i+1} ({mime_type}, {actual_size_mb:.1f}MB)")
                            
                            # Clear image_data from memory immediately
                            del image_data
                            
                        else:
                            print(f"⚠️ Failed to download image {i+1}: HTTP {response.status}")
                            
                except Exception as e:
                    print(f"❌ Error processing image {i+1} ({image_url}): {str(e)}")
                    continue
    
    finally:
        # Clean up any temporary files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    print(f"🗑️ Cleaned up temporary file: {temp_file}")
            except Exception as e:
                print(f"⚠️ Error cleaning up temp file {temp_file}: {e}")
    
    print(f"🖼️ Successfully processed {len(image_parts)} out of {len(profileImages)} images")
    return image_parts


async def get_final_response(runner: Runner, user_id: str, session_id: str, message: str, image_parts: List[types.Part] = None) -> str:
    """
    Get final response from agent using ADK best practices.
    
    Args:
        runner: ADK Runner instance
        user_id: User ID
        session_id: Session ID (must already exist)
        message: User message text
        image_parts: Optional list of image Parts
        
    Returns:
        str: Final response text from agent
    """
    final_response_text = "Agent did not produce a final response."
    all_events = []
    
    try:
        # Prepare new_message for ADK runner - always use Content format
        if image_parts:
            print(f"🖼️ Including {len(image_parts)} images with the message")
            # Create multimodal content when images are present
            parts = [types.Part.from_text(text=message)]
            parts.extend(image_parts)
        else:
            # Create text-only content
            parts = [types.Part.from_text(text=message)]
        
        # Always construct Content object for consistent ADK framework compatibility
        new_message = types.Content(role="user", parts=parts)
        
        # Execute agent workflow
        print(f"🚀 Starting agent execution for user={user_id}, session={session_id}")
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message
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
        # raise
    finally:
        # Clean up image_parts from memory after processing
        if image_parts:
            print(f"🧹 Cleaning up {len(image_parts)} image parts from memory")
            image_parts.clear()
            del image_parts

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
    profileImages: Optional[List[str]] = None

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
    image_parts = []  # Initialize outside try block for cleanup
    try:
        import time
        start_time = time.time()
        print(f"🔍 Request: {request}")
        
        # 首先处理profileImages（在创建session之前）
        if request.profileImages:
            print(f"🖼️ Found {len(request.profileImages)} profile images to process")
            image_parts = await process_profileImages(request.profileImages)
        else:
            print("📷 No profile images provided")
        
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
                    "inquiry_email": "None",
                    "has_profileImages": len(image_parts) > 0,  # 标记是否有图片
                    "profileImages_count": len(image_parts)      # 图片数量
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
        
        # 构造触发消息，包含图片信息
        # if image_parts:
        #     trigger_message = f"Please follow your instructions(system prompt) to start analyzing. I'm providing {len(image_parts)} profile images for creator's social media analytics and supplemental information from one or multiple platforms. Please analyze these images along with other profile data to provide comprehensive insights. These images are for the creator's profile, not the brand's."
        # else:
        #     trigger_message = "Please follow your instructions(system prompt) to start analyzing."
        trigger_message = f"""
        Please follow your instructions(system prompt) to start analyzing.
        - Brand name: {initial_state["brand_name"]},
        - Youtube creator profile: {initial_state["youtube_creator_profile"]}
        - Optional: {len(image_parts) if image_parts else 0} images(screenshots) as supplemental information of the CREATOR's profile, not BRAND's.
        """
        # 获取最终响应（agent会从session state中读取参数，同时接收图片内容）
        final_response_text = await get_final_response(
            deal_runner, 
            request.userId, 
            request.sessionId, 
            trigger_message,
            image_parts  # 传递图片parts
        )
        
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
        
        # 创建响应对象
        response_data = DealAnalysisResponse(
            success=True,
            dealId=request.sessionId,
            analysis=analysis_data,
            executionTime=execution_time
        )
        
        # 发送结果到webhook
        webhook_url = "https://xgyslewfwwlyknuhlols.supabase.co/functions/v1/update-deal-status"
        webhook_headers = {
            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhneXNsZXdmd3dseWtudWhsb2xzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAyNjY3OTYsImV4cCI6MjA2NTg0Mjc5Nn0.hgBdE8_2oiR1OM5rNHIFOhN56OhfCZre7g8WcwYaQUs',
            'Content-Type': 'application/json'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url, 
                    json=response_data.model_dump(),
                    headers=webhook_headers
                ) as response:
                    if response.status == 200:
                        print(f"✅ Successfully sent data to webhook: {webhook_url}")
                    else:
                        response_text = await response.text()
                        print(f"⚠️ Webhook request failed with status {response.status}: {response_text}")
        except Exception as e:
            print(f"❌ Error sending data to webhook: {str(e)}")
            # webhook失败不影响主流程，继续返回结果
        
        return response_data
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Deal analysis failed: {type(e).__name__}: {str(e)}")
    finally:
        # Clean up image_parts from memory after processing
        if image_parts:
            print(f"🧹 Cleaning up {len(image_parts)} image parts from deal analysis endpoint")
            image_parts.clear()




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