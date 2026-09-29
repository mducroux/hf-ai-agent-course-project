"""Clients for the Hugging Face models used to understand images and audio."""
import base64
import mimetypes
from pathlib import Path

from huggingface_hub import InferenceClient

from config import get_hf_token

VISION_MODEL = "Qwen/Qwen2.5-VL-72B-Instruct"
SPEECH_MODEL = "openai/whisper-large-v3"


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
