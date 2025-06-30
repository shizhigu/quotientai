# from google.adk.agents.llm_agent import LlmAgent
# import datetime
# from state_keys import STATE_YOUTUBE_CREATOR_PROFILE


# async def get_creator_profile(youtubeId: str, platform: str):
#     """
#     通过API获取YouTuber的核心数据指标
    
#     Args:
#         youtubeId: YouTube频道ID (如 UCm-X6o81nRsXQTmqpyArkBQ)
#         platform: 平台名称 (如 "YouTube")
    
#     Returns:
#         dict: 包含核心数据指标的结构化信息
#     """
#     try:
#         import aiohttp
        
#         # API配置
#         url = f"https://dev.creatordb.app/v2/youtubeDetail?youtubeId={youtubeId}"
#         headers = {
#             'Accept': 'application/json',
#             'apiId': 'b3e3a97d2e6f09e2-wh0AJmeBdyX5XSBofqwo'
#         }
        
#         # 调用API获取数据
#         async with aiohttp.ClientSession() as session:
#             async with session.get(url, headers=headers) as response:
#                 if response.status != 200:
#                     return {
#                         "error": f"API request failed with status {response.status}",
#                         "youtubeId": youtubeId,
#                         "platform": platform
#                     }
                
#                 data = await response.json()
        
#         # 检查API响应
#         if not data.get("success", False):
#             return {
#                 "error": f"API returned error: {data.get('error', 'Unknown error')}",
#                 "youtubeId": youtubeId,
#                 "platform": platform
#             }
        
#         basic = data["data"]["basicYoutube"]
#         detail = data["data"]["detailYoutube"]
        
#         # 提取核心数据，保持原始性
#         creator_profile = {
#             # 基本信息
#             "channel_name": basic["youtubeName"],
#             "display_id": basic["displayId"],
#             "youtubeId": youtubeId,
#             "platform": platform,
#             "content_category": basic["mainCategory"],
#             "primary_country": basic["country"],
#             "primary_language": basic["lang"],
#             "has_business_email": basic["hasEmail"],
            
#             # 规模指标
#             "total_subscribers": basic["subscribers"],
#             "total_lifetime_views": basic["views"],
#             "avg_views_per_video_1year": basic["avgViews1Y"],
#             "avg_likes_per_video_1year": basic["avgLikes1Y"],
#             "avg_comments_per_video_1year": basic["avgComments1Y"],
#             "avg_video_length_seconds": basic["avgLength1Y"],
            
#             # 参与度指标
#             "engagement_rate_1year": round(basic["engageRate1Y"], 3),
#             "engagement_rate_recent_20_videos": round(basic["engageRateR20"], 3),
            
#             # 增长指标 (百分比字符串)
#             "subscriber_growth_rate": f"{basic['gRateSubscribers'] * 100:.2f}%",
#             "views_growth_rate": f"{basic['gRateViews'] * 100:.2f}%",
            
#             # 发布频率
#             "videos_published_last_30_days": detail["videosIn30Days"],
#             "videos_published_last_90_days": detail["videosIn90Days"],
            
#             # 受众人口统计
#             "audience_primary_country": detail["ytDgMainCountry"],
#             "audience_country_concentration_ratio": round(detail["ytDgMainCountryRatio"], 3),
#             "audience_male_percentage": round(detail["ytDgGenderMaleRatio"], 3),
#             "audience_female_percentage": round(detail["ytDgGenderFemaleRatio"], 3),
#             "audience_average_age": round(detail["ytDgAvgAge"], 3),
            
#             # 平台排名
#             "platform_overall_score": round(detail["ranking"]["score"], 3),
#             "subscriber_ranking_percentile": round(detail["ranking"]["subscribers"], 3),
            
#             # 时间信息
#             "channel_creation_date": datetime.datetime.fromtimestamp(basic["createDate"] / 1000).strftime('%Y-%m-%d') if basic["createDate"] else None,
#             "last_video_upload_date": datetime.datetime.fromtimestamp(basic["lastUploadTime"] / 1000).strftime('%Y-%m-%d') if basic["lastUploadTime"] else None,
#             # "channel_creation_timestamp": basic["createDate"],
#             # "last_video_upload_timestamp": basic["lastUploadTime"]
#         }
        
#         return creator_profile
        
#     except Exception as e:
#         return {
#             "error": f"Data extraction failed: {str(e)}",
#             "youtubeId": youtubeId,
#             "platform": platform
#         }


# class CreatorProfileFetchAgent(LlmAgent):
#     def __init__(self):
#         super().__init__(
#             model="gemini-2.0-flash",
#             name="CreatorProfileFetchAgent",
#             instruction=f"""
#                 You are a data analyst for a content creator. You are an expert in documenting creator's profile.
#                 Once you are given a creator's profile, you need to document the profile in the original format.
#             """,
#             output_key=STATE_YOUTUBE_CREATOR_PROFILE
#         )

# creator_profile_fetch_agent = CreatorProfileFetchAgent()