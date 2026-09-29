"""Download the files attached to some course questions."""
import tempfile
from pathlib import Path

import requests
from huggingface_hub import hf_hub_download

from config import get_hf_token

API_URL = "https://agents-course-unit4-scoring.hf.space"
GAIA_REPO = "gaia-benchmark/GAIA"
CACHE_DIR = Path(tempfile.gettempdir()) / "agent_attachments"


def download_attachment(task_id: str, file_name: str) -> Path:
    """Fetch the file from the scoring API, or from the GAIA dataset if the API has none."""
    target = CACHE_DIR / file_name
    if target.exists():
        return target

    response = requests.get(f"{API_URL}/files/{task_id}", timeout=30)
    if response.ok:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        target.write_bytes(response.content)
        return target

    for split in ("validation", "test"):
        try:
            path = hf_hub_download(
                GAIA_REPO,
                f"2023/{split}/{file_name}",
                repo_type="dataset",
                token=get_hf_token(),
            )
            return Path(path)
        except Exception:
            continue

    raise FileNotFoundError(
        f"{file_name} is not served by the scoring API (HTTP {response.status_code}) and could "
        f"not be downloaded from {GAIA_REPO}. That dataset is gated: accept its terms at "
        f"https://huggingface.co/datasets/{GAIA_REPO} with the account that owns your token."
    )
