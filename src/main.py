from dotenv import load_dotenv
load_dotenv()

import time
from utils.logger import get_logger
from audio.wake import listen_for_wake_word
from audio.listen import listen_until_silence 
from agent.llm import ask_llm
from agent.tools.play_music import YouTubePlayer
from hardware.led import blue_led_on, blue_led_off
from config import BLUE_LED_PIN

logger = get_logger(__name__)
logger.info("Starting Assistant...")


def main() -> None:
    listen_for_wake_word(after_wake)


def after_wake() -> None:
    logger.info("Wake word detected! Listening for command...")
    try:
        blue_led_on(BLUE_LED_PIN)
    except Exception:
        pass
    YouTubePlayer.stop()
    time.sleep(0.5)
    speech = listen_until_silence()
    logger.info(f"Speech detected! {speech}")
    # Immediately free the pin before TTS so say.py can animate on same pin
    try:
        blue_led_off()
    except Exception:
        pass
    ask_llm(speech)

try:
    while True:
        main()
    logger.info("Assistant stopped.")
except KeyboardInterrupt:
    logger.info("Received KeyboardInterrupt. Assistant stopped.")
