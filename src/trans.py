import os
import yt_dlp
from deepgram import Deepgram
from .config import Config

_dg_client = None  # lazy singleton

def _get_deepgram_client() -> Deepgram:
    """Get Deepgram client, creating it lazily on first use"""
    global _dg_client
    if _dg_client is None:
        cfg = Config()
        key = (cfg.DEEPGRAM_API_KEY or os.getenv("DEEPGRAM_API_KEY", "")).strip()
        if not key:
            raise RuntimeError("DEEPGRAM_API_KEY not set in Config or environment.")
        _dg_client = Deepgram(key)
    return _dg_client

def download_youtube_audio(youtube_url, output_dir="downloads"):
    """Download YouTube video as WAV audio file"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract video ID properly, handling URL parameters
    if 'v=' in youtube_url:
        video_id = youtube_url.split('v=')[1].split('&')[0]
    elif 'youtu.be/' in youtube_url:
        video_id = youtube_url.split('youtu.be/')[1].split('?')[0]
    else:
        # Fallback: use last part of URL
        video_id = youtube_url.split('/')[-1].split('?')[0]
    
    # Use absolute path to avoid working directory issues
    abs_output_dir = os.path.abspath(output_dir)
    output_template = os.path.join(abs_output_dir, f"{video_id}.%(ext)s")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }]
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            final_path = os.path.join(abs_output_dir, f"{info['id']}.wav")
            
            # Check if file actually exists
            if os.path.exists(final_path):
                return final_path
            else:
                # Try alternative naming patterns
                alt_path = os.path.join(abs_output_dir, f"{video_id}.wav")
                if os.path.exists(alt_path):
                    return alt_path
                
                # List files for debugging
                files = os.listdir(abs_output_dir) if os.path.exists(abs_output_dir) else []
                raise FileNotFoundError(f"WAV file not found. Expected: {final_path}, Files in directory: {files}")
                
    except Exception as e:
        raise Exception(f"Error downloading YouTube audio: {str(e)}")

async def transcribe_audio(file_path):
    """Transcribe audio file using Deepgram"""
    client = _get_deepgram_client()  # Get client lazily
    
    with open(file_path, 'rb') as audio_file:
        source = {'buffer': audio_file, 'mimetype': 'audio/wav'}
        response = await client.transcription.prerecorded(source, {'punctuate': True})
        return response['results']['channels'][0]['alternatives'][0]['transcript']

async def youtube_to_transcript(youtube_url):
    """Download YouTube video and convert to transcript"""
    wav_file = None
    try:
        # Step 1: Download audio from YouTube
        print(f"Downloading audio from: {youtube_url}")
        wav_file = download_youtube_audio(youtube_url)
        print(f"Audio downloaded to: {wav_file}")
        
        # Step 2: Transcribe the audio using Deepgram
        print("Starting transcription...")
        transcript = await transcribe_audio(wav_file)
        print(f"Transcription complete. Length: {len(transcript) if transcript else 0} characters")
        
        # Step 3: Clean up the wav file
        if wav_file and os.path.exists(wav_file):
            os.remove(wav_file)
            print(f"Cleaned up audio file: {wav_file}")
            
        return transcript
        
    except Exception as e:
        # Clean up file even if transcription fails
        if wav_file and os.path.exists(wav_file):
            try:
                os.remove(wav_file)
                print(f"Cleaned up audio file after error: {wav_file}")
            except:
                pass
        
        print(f"Error in youtube_to_transcript: {str(e)}")
        raise Exception(f"Error processing transcript: {str(e)}")

