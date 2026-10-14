# /// script
# dependencies = ["huggingface_hub"]
# ///
"""Publish model repo + demo Space. Needs HF_TOKEN (write) or `hf auth login`. Run: uv run deploy.py"""
import shutil
import tempfile
from pathlib import Path
from huggingface_hub import HfApi

api = HfApi()
user = api.whoami()["name"]
here = Path(__file__).parent

with tempfile.TemporaryDirectory() as d:
    model, space = Path(d, "model"), Path(d, "space")
    model.mkdir(), space.mkdir()
    for f in ["model.safetensors", "flip2.py", "train.py", "results.json", "loss.png", "media/flip-2-launch.mp4", "media/poster.jpg"]:
        shutil.copy(here / f, model / Path(f).name)
    (model / "README.md").write_text((here / "MODEL_CARD.md").read_text().replace("{user}", user))
    for f in ["index.html", "README.md"]:
        shutil.copy(here / "space" / f, space / f)
    shutil.copy(here / "model.safetensors", space / "model.safetensors")

    api.create_repo(f"{user}/flip-2", exist_ok=True)
    api.upload_folder(folder_path=model, repo_id=f"{user}/flip-2")
    api.create_repo(f"{user}/flip-2", repo_type="space", space_sdk="static", exist_ok=True)
    api.upload_folder(folder_path=space, repo_id=f"{user}/flip-2", repo_type="space")

print(f"https://huggingface.co/{user}/flip-2")
print(f"https://huggingface.co/spaces/{user}/flip-2")
