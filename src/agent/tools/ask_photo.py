import base64
from picamzero import Camera
from PIL import Image
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from utils.logger import get_logger
from agent.prompts import CAMERA_PROMPT

logger = get_logger(__name__)
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

@tool
def ask_photo() -> str:
    """
    Takes photo and gives whats in it
    """
    try:
        logger.info("Capturing photo with picamzero.Camera...")

        cam = Camera()
        photo_path = "helloworld.jpg"
        cam.take_photo(photo_path)

        img = Image.open(photo_path)
        rotated_img = img.rotate(180)
        rotated_img.save(photo_path)

        with open(photo_path, "rb") as f:
            photo_bytes = f.read()
        photo_b64 = base64.b64encode(photo_bytes).decode("utf-8")
        logger.info("Photo captured")

        messages = [
            SystemMessage(content=CAMERA_PROMPT),
            HumanMessage(content=[{
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{photo_b64}"
                }
            }])
        ]
        response = model.invoke(messages)
        return response.content
    except Exception as e:
        logger.error("Error capturing or analyzing photo: %s", e)
        return f"Error capturing or analyzing photo: {e}"
