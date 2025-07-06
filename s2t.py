from openai import OpenAI
from datetime import timedelta
# import os
# client = OpenAI()
# audio_file= open("videoplayback.mp3", "rb")


# from pydub import AudioSegment

# song = AudioSegment.from_mp3("videoplayback.mp3")

# # PyDub handles time in milliseconds
# ten_minutes = 5 * 60 * 1000

# first_10_minutes = song[:ten_minutes]

# first_10_minutes.export("videoplayback_10.mp3", format="mp3")



from elevenlabs import ElevenLabs
from dotenv import load_dotenv
import os
load_dotenv()

client = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
)

audio_file= open("videoplayback_10.mp3", "rb")

transcription = client.speech_to_text.convert(
    model_id="scribe_v1",
    file=audio_file,
    diarize=True,
)
print(transcription)





# audio_file= open("videoplayback_10.mp3", "rb")


# transcription = client.audio.transcriptions.create(
#   file=audio_file,
#   model="whisper-1",
#   response_format="verbose_json",
#   timestamp_granularities=["segment"]
# )

# segments = transcription.segments

# for segment in segments:
#         startTime = segment.start # str(0)+str(timedelta(seconds=int(segment.start)))+',000'
#         endTime = segment.end # str(0)+str(timedelta(seconds=int(segment.end)))+',000'
#         text = segment.text
#         print(startTime, endTime, text)
#         segmentId = segment.id+1
#         segment = f"{segmentId}\n{startTime} --> {endTime}\n{text[1:] if text[0] is ' ' else text}\n\n"

#         srtFilename = "videoplayback_10.srt"
#         with open(srtFilename, 'w', encoding='utf-8') as srtFile:
#             srtFile.write(segment)
