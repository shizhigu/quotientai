#!/usr/bin/env python3
"""
Example usage of the Complete Video Segment Selection Pipeline

This demonstrates the full workflow:
YouTube URL → Audio Download → Deepgram Transcription → LLM Segment Selection
"""

import json
import requests

# Example API request - just a YouTube URL!
example_request = {
    "userId": "user123",
    "sessionId": "video_session_456", 
    "youtubeUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "processingMode": "marketing",
    "targetDuration": 45
}

# Expected output format from the complete pipeline
expected_output = {
    "success": True,
    "sessionId": "video_session_456",
    "selectedSegments": [
        {
            "start": 15.2,
            "end": 28.7,
            "duration": 13.5,
            "text": "This one simple framework increased our sales by 340% in just two weeks",
            "reason": "Strong social proof with specific, impressive results for marketing content",
            "engagement_score": 9,
            "standalone_value": True
        },
        {
            "start": 45.1,
            "end": 58.3,
            "duration": 13.2,
            "text": "The three secrets that helped me grow from zero to six figures in 18 months",
            "reason": "Compelling hook with specific timeline and results, perfect for marketing",
            "engagement_score": 8,
            "standalone_value": True
        },
        {
            "start": 78.4,
            "end": 89.9,
            "duration": 11.5,
            "text": "Most entrepreneurs make this one critical mistake that's costing them millions",
            "reason": "Problem-focused statement that creates urgency and positions expertise",
            "engagement_score": 7,
            "standalone_value": True
        }
    ],
    "totalDuration": 38.2,
    "segmentCount": 3,
    "processingMode": "marketing",
    "executionTime": 23.4
}

def example_api_call():
    """Example of how to call the API"""
    try:
        response = requests.post(
            "http://localhost:8000/custom/video/select-segments",
            json=example_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"Selected {result['segmentCount']} segments")
            print(f"Total duration: {result['totalDuration']:.1f} seconds")
            
            for i, segment in enumerate(result['selectedSegments'], 1):
                print(f"\nSegment {i}:")
                print(f"  Time: {segment['start']:.1f}s - {segment['end']:.1f}s")
                print(f"  Text: {segment['text']}")
                print(f"  Reason: {segment['reason']}")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

print("🎬 Complete Video Segment Selection Pipeline")
print("=" * 60)
print("\n🔄 Full Workflow:")
print("1. 📺 YouTube URL Input")
print("2. 🎵 Audio Download (yt-dlp)")  
print("3. 🎤 Deepgram Transcription (word-level)")
print("4. 🧠 LLM Segment Selection (pure intelligence)")
print("5. 📋 Structured JSON Output")

print(f"\n📥 User Input (Simple!):")
print("POST /custom/video/select-segments")
print(json.dumps(example_request, indent=2))

print(f"\n📤 Expected Output:")
print(json.dumps(expected_output, indent=2))

print(f"\n🎯 Key Benefits:")
print("• Just provide YouTube URL - we handle everything else")
print("• Deepgram provides precise word-level timestamps")  
print("• LLM uses semantic understanding, not keyword matching")
print("• Mode-specific selection (marketing, tutorial, highlights, etc.)")
print("• Ready-to-use timestamps for video segment extraction")

print(f"\n🚀 Example Usage:")
print("```python")
print("import requests")
print("")
print("response = requests.post(")
print("    'http://localhost:8000/custom/video/select-segments',")
print("    json={")
print(f"        'youtubeUrl': '{example_request['youtubeUrl']}',")
print(f"        'processingMode': '{example_request['processingMode']}',")
print(f"        'targetDuration': {example_request['targetDuration']},")
print(f"        'userId': '{example_request['userId']}',")
print(f"        'sessionId': '{example_request['sessionId']}'")
print("    }")
print(")")
print("")
print("segments = response.json()['selectedSegments']")
print("# Use the start/end times to extract video clips!")
print("```")

print(f"\n💡 Next Steps After Getting Segments:")
print("1. Use start/end times with yt-dlp to download specific video clips")
print("2. Apply branding, subtitles, and effects")
print("3. Concatenate clips into final short-form video")
print("4. Export for social media platforms")

# Uncomment to test with real API:
# example_api_call()