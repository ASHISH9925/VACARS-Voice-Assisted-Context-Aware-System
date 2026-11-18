from typing import List
import os

from google import genai
from google.genai import types
from langchain_core.tools import tool

from utils.logger import get_logger


logger = get_logger(__name__)

# Prefer GOOGLE_API_KEY if present; otherwise fall back to ADC.
_api_key = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=_api_key) if _api_key else genai.Client()


@tool
def google_search(query: str) -> str:
	"""
	Perform a grounded Google web search via Gemini and return the model's
	concise answer along with top citations.

	- Input: query string
	- Output: answer text with numbered sources appended
	"""
	try:
		grounding_tool = types.Tool(google_search=types.GoogleSearch())
		config = types.GenerateContentConfig(tools=[grounding_tool])
		resp = client.models.generate_content(
			model="gemini-2.5-flash",
			contents=query,
			config=config,
		)
		answer = resp.text or "No answer"
		# Collect citations if present
		citations: List[str] = []
		try:
			meta = resp.candidates[0].grounding_metadata
			chunks = getattr(meta, "grounding_chunks", []) or []
			for chunk in chunks[:5]:
				uri = getattr(chunk, "uri", None) or getattr(chunk, "web", {}).get("uri") if hasattr(chunk, "web") else None
				title = getattr(chunk, "title", None) or getattr(chunk, "web", {}).get("title") if hasattr(chunk, "web") else None
				if uri or title:
					label = title or uri or "source"
					citations.append(f"- {label}: {uri}")
		except Exception:
			pass
		if citations:
			answer = f"{answer}\n\nSources:\n" + "\n".join(citations)
		return answer
	except Exception as e:
		logger.error(f"Google search error: {e}")
		return f"Error during google_search: {str(e)}"


