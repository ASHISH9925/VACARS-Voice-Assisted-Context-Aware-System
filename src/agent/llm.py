from audio.say import say
from config import MODEL
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
"""Lightweight in-file chat memory to avoid external memory dependencies."""

from utils.logger import get_logger
from agent.prompts import BASE_PROMPT

from agent.tools.play_music import play_music
from agent.tools.send_email import send_email
from agent.tools.ask_photo import ask_photo
from agent.tools.google_search import google_search
from agent.tools.remove_frontplate import remove_frontplate


logger = get_logger(__name__)
logger.info(f"Using model: {MODEL}")
model = init_chat_model(MODEL, model_provider="google_genai")


class _ChatMemory:
	def __init__(self) -> None:
		self.messages = []

	def add_message(self, message) -> None:
		self.messages.append(message)


class SimpleMemory:
	def __init__(self) -> None:
		self.chat_memory = _ChatMemory()


memory = SimpleMemory()


@tool
def get_name() -> str:
    """
    Returns your name
    """
    return "Fackasur, the fake devil"


agent = create_react_agent(
    model=model,
    tools=[get_name, play_music, send_email, ask_photo, google_search, remove_frontplate],
    prompt=BASE_PROMPT,
)


def ask_llm(message: str) -> None:
    memory.chat_memory.add_message(HumanMessage(content=message))
    response = agent.invoke({"messages": memory.chat_memory.messages})
    ai_res = response.get("messages")[-1].content
    memory.chat_memory.add_message(AIMessage(content=ai_res))
    logger.info(f"LLM response: {ai_res}")
    def _content_to_text(content) -> str:
    	if isinstance(content, str):
    		return content
    	if isinstance(content, list):
    		parts = []
    		for part in content:
    			if isinstance(part, dict):
    				text = part.get("text") or part.get("content")
    				if text:
    					parts.append(str(text))
    				continue
    			text_attr = getattr(part, "text", None)
    			if text_attr:
    				parts.append(str(text_attr))
    		return " ".join(parts).strip()
    	return str(content)

    say(_content_to_text(ai_res))
