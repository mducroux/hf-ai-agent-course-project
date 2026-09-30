"""The Hugging Face models used by the agent: the chat LLM, plus vision and speech clients."""
import base64
import mimetypes
from pathlib import Path

from huggingface_hub import InferenceClient
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

from config import get_hf_token

CHAT_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
VISION_MODEL = "Qwen/Qwen2.5-VL-72B-Instruct"
SPEECH_MODEL = "openai/whisper-large-v3"


def build_chat(tools):
    """Return the chat model with `tools` bound, retrying on network errors and timeouts."""
    llm = HuggingFaceEndpoint(
        repo_id=CHAT_MODEL, huggingfacehub_api_token=get_hf_token(), timeout=30
    )
    # Binding an empty tool list can be rejected by the API, so only bind real tools.
    chat = ChatHuggingFace(llm=llm)
    chat = chat.bind_tools(tools) if tools else chat
    # Network errors and timeouts happen; retry instead of failing the question.
    return chat.with_retry(stop_after_attempt=3)


def describe_image(path: Path, instruction: str) -> str:
    """Ask the vision model `instruction` about the image at `path`."""
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    data = base64.b64encode(path.read_bytes()).decode()
    response = InferenceClient(token=get_hf_token(), timeout=60).chat.completions.create(
        model=VISION_MODEL,
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}},
                    {"type": "text", "text": instruction},
                ],
            }
        ],
    )
    return response.choices[0].message.content


def transcribe_audio(path: Path) -> str:
    """Transcribe the speech in the audio file at `path`."""
    client = InferenceClient(token=get_hf_token(), timeout=120)
    return client.automatic_speech_recognition(str(path), model=SPEECH_MODEL).text
