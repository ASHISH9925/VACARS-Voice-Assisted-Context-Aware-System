import speech_recognition as sr
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

def listen_until_silence(timeout: int = 20) -> Optional[str]:
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        logger.info("Adjusting for ambient noise... Please stay quiet.")
        recognizer.adjust_for_ambient_noise(source, duration=0.7)
        logger.info("Listening... Speak now!")
        
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=30)
            
            logger.info("Processing speech...")
            
            text = recognizer.recognize_google(audio)
            logger.info(f"Recognized: {text}")
            return text
            
        except sr.WaitTimeoutError:
            logger.info("No speech detected within timeout period.")
            return None
        except sr.UnknownValueError:
            logger.info("Could not understand the audio.")
            return None
        except sr.RequestError as e:
            logger.info(f"Could not request results from speech recognition service; {e}")
            return None
        except Exception as e:
            logger.info(f"An error occurred: {e}")
            return None