from langchain_core.tools import tool
from enum import Enum
import yt_dlp
import subprocess
import threading
import requests

from typing import Optional, Dict, Any

from utils.logger import get_logger

logger = get_logger(__name__)


class PlayerState(Enum):
    PLAYING = "PLAYING"
    STOPPED = "STOPPED"
    PAUSED = "PAUSED"


class YouTubePlayer:
    
    player_state = PlayerState.STOPPED
    current_process : Optional[subprocess.Popen] = None
    playing_thread : Optional[threading.Thread] = None

    ytdl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "default_search": "ytsearch",
        "extract_flat": False,
    }
    
    @staticmethod
    def _get_best_audio_format(formats: list) -> Optional[Dict[str, Any]]:
        audio_formats = []

        # First, try to get pure audio formats (no video)
        for fmt in formats:
            if fmt.get("acodec") != "none" and fmt.get("vcodec") == "none":
                audio_formats.append(fmt)

        # If no pure audio formats, get any format with audio
        if not audio_formats:
            for fmt in formats:
                if fmt.get("acodec") != "none":
                    audio_formats.append(fmt)

        if not audio_formats:
            return None

        def sort_key(fmt):
            # Prioritize by quality metrics rather than specific extensions
            abr = fmt.get("abr", 0) or 0  # Audio bitrate
            asr = fmt.get("asr", 0) or 0  # Audio sample rate
            ext = fmt.get("ext", "").lower()
            acodec = fmt.get("acodec", "").lower()
            
            # Quality score based on bitrate and sample rate
            quality_score = abr * 0.7 + asr * 0.3
            
            # Extension preference (but not strict)
            if ext in ["webm", "m4a", "mp4"]:
                ext_priority = 2
            elif ext in ["mp3", "aac", "ogg"]:
                ext_priority = 1
            else:
                ext_priority = 0
            
            # Codec preference
            if "opus" in acodec or "aac" in acodec:
                codec_priority = 2
            elif "mp3" in acodec:
                codec_priority = 1
            else:
                codec_priority = 0
            
            # Return tuple for sorting: (quality_score, ext_priority, codec_priority)
            return (-quality_score, -ext_priority, -codec_priority)

        audio_formats.sort(key=sort_key)
        return audio_formats[0]
    
    @staticmethod
    def _get_alternative_audio_formats(formats: list) -> list:
        """Get alternative audio formats sorted by preference"""
        audio_formats = []

        # Get all formats with audio
        for fmt in formats:
            if fmt.get("acodec") != "none":
                audio_formats.append(fmt)

        if not audio_formats:
            return []

        def sort_key(fmt):
            abr = fmt.get("abr", 0) or 0
            asr = fmt.get("asr", 0) or 0
            ext = fmt.get("ext", "").lower()
            acodec = fmt.get("acodec", "").lower()
            
            quality_score = abr * 0.7 + asr * 0.3
            
            # Prefer more common/stable formats for fallback
            if ext in ["mp3", "m4a", "mp4"]:
                ext_priority = 3
            elif ext in ["webm", "aac"]:
                ext_priority = 2
            elif ext in ["ogg"]:
                ext_priority = 1
            else:
                ext_priority = 0
            
            if "mp3" in acodec or "aac" in acodec:
                codec_priority = 2
            elif "opus" in acodec:
                codec_priority = 1
            else:
                codec_priority = 0
            
            return (-quality_score, -ext_priority, -codec_priority)

        audio_formats.sort(key=sort_key)
        return audio_formats
    
    @staticmethod
    def _search_youtube(query: str) -> Dict[str, Any]:
        """Search YouTube for a query and return video info"""
        try:
            search_url = f"ytsearch:{query}"
            with yt_dlp.YoutubeDL(YouTubePlayer.ytdl_opts) as ydl:
                info = ydl.extract_info(search_url, download=False)
                if "entries" in info and info["entries"]:
                    return info["entries"][0]
                else:
                    raise Exception(f"Could not find music for query: {query}")
        except Exception as e:
            logger.error(f"Error searching YouTube: {e}")
            raise
    
    @staticmethod
    def _get_video_info_from_url(url: str) -> Dict[str, Any]:
        try:
            with yt_dlp.YoutubeDL(YouTubePlayer.ytdl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as e:
            logger.error(f"Error getting video info from URL: {e}")
            raise
    
    @staticmethod
    def _validate_audio_url(audio_url: str) -> bool:
        """Validate if the audio URL is accessible"""
        try:
            response = requests.head(audio_url, timeout=10, allow_redirects=True)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Could not validate audio URL: {e}")
            return True  # Assume it's valid if we can't check
    
    @staticmethod
    def _play_audio(audio_url: str) -> None:
        try:
            def _worker():
                try:
                    # Validate URL before attempting playback
                    if not YouTubePlayer._validate_audio_url(audio_url):
                        logger.error("Audio URL is not accessible (403 Forbidden or similar)")
                        return
                    
                    YouTubePlayer.current_process = subprocess.Popen([
                        "ffplay",
                        "-nodisp",
                        "-autoexit",
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        audio_url,
                    ])
                    YouTubePlayer.current_process.wait()
                except Exception as inner_e:
                    logger.error(f"Error in playback worker: {inner_e}")
                finally:
                    YouTubePlayer.current_process = None
                    YouTubePlayer.player_state = PlayerState.STOPPED
                    YouTubePlayer.playing_thread = None

            thread = threading.Thread(target=_worker, daemon=True)
            YouTubePlayer.playing_thread = thread
            thread.start()
        except Exception as e:
            logger.error(f"Error starting audio playback: {e}")
            raise
    
    @staticmethod
    def play(query: Optional[str] = None) -> str:
        if YouTubePlayer.player_state == PlayerState.PLAYING:
            return "Already playing music. Please stop current playback first."
        
        try:
            YouTubePlayer.player_state = PlayerState.PLAYING
            
            if query:
                video_info = YouTubePlayer._search_youtube(query)
            else:
                url = "https://www.youtube.com/watch?v=ZflUh97INAM"
                video_info = YouTubePlayer._get_video_info_from_url(url)
            
            formats = video_info.get("formats", [])
            best_format = YouTubePlayer._get_best_audio_format(formats)
            
            if not best_format:
                return "No suitable audio format found"
            
            # Try the best format first
            audio_url = best_format["url"]
            title = video_info.get("title", "Unknown")
            duration = video_info.get("duration", 0)
            
            logger.info(f"Playing: {title}")
            logger.info(f"Duration: {duration} seconds")
            logger.info(f"Format: {best_format.get('format_note', 'Unknown')}")
            logger.info(f"Bitrate: {best_format.get('abr', 'Unknown')} kbps")
            
            # Validate the URL before attempting playback
            if not YouTubePlayer._validate_audio_url(audio_url):
                logger.warning("Primary audio URL not accessible, trying alternatives...")
                
                # Try alternative formats
                alternative_formats = YouTubePlayer._get_alternative_audio_formats(formats)
                for alt_format in alternative_formats:
                    if alt_format.get("url") != audio_url:  # Don't try the same URL again
                        alt_url = alt_format.get("url")
                        if alt_url and YouTubePlayer._validate_audio_url(alt_url):
                            logger.info(f"Using alternative format: {alt_format.get('format_note', 'Unknown')}")
                            audio_url = alt_url
                            break
                else:
                    logger.error("No accessible audio formats found")
                    YouTubePlayer.player_state = PlayerState.STOPPED
                    return "Error: No accessible audio formats found. The video may be restricted or unavailable."
            
            YouTubePlayer._play_audio(audio_url)
            return f"Playing: {title}"
            
        except Exception as e:
            YouTubePlayer.player_state = PlayerState.STOPPED
            logger.error(f"Error playing music: {e}")
            return f"Error playing music: {str(e)}"
    
    @staticmethod
    def stop() -> str:
        if YouTubePlayer.player_state != PlayerState.PLAYING:
            return "No music is currently playing"
        
        try:
            if YouTubePlayer.current_process:
                try:
                    YouTubePlayer.current_process.terminate()
                except Exception:
                    pass
                finally:
                    try:
                        YouTubePlayer.current_process.kill()
                    except Exception:
                        pass
                    YouTubePlayer.current_process = None

            if YouTubePlayer.playing_thread and YouTubePlayer.playing_thread.is_alive():
                YouTubePlayer.playing_thread.join(timeout=1.0)
                YouTubePlayer.playing_thread = None

            YouTubePlayer.player_state = PlayerState.STOPPED
            return "Music playback stopped"
        except Exception as e:
            logger.error(f"Error stopping music: {e}")
            return f"Error stopping music: {str(e)}"
    


_player = YouTubePlayer()


@tool
def play_music(query: str = None) -> str:
    """
    Plays music from YouTube. If no query is provided, plays a default song.

    Args:
        query: Search query for music to play. If None, plays default music.
        You must transform query if required
    """
    return _player.play(query)
