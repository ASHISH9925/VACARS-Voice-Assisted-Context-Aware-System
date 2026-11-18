import pyaudio
import numpy as np

from utils.logger import get_logger
from typing import Callable
from pvporcupine import create
from os import getenv

WAKE_WORDS = [
    "jarvis",
]

logger = get_logger(__name__)

porcupine = create(
    access_key=getenv("PORCUPINE_ACCESS_KEY"),
    keywords=WAKE_WORDS,
    sensitivities=[0.1],
)
pa = pyaudio.PyAudio()

stream = pa.open(
    rate=porcupine.sample_rate,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=porcupine.frame_length,
)


def listen_for_wake_word(callback: Callable[[], None]) -> None:
    logger.info(f"Listening for wake words: {WAKE_WORDS}")
    while True:
        try:
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = np.frombuffer(pcm, dtype=np.int16)
            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                callback()
                break
        except Exception as e:
            logger.error(f"Error: {e}")
            continue
