import ollama
import base64
import subprocess
import time
from pathlib import Path


def ensure_ollama_running():
    try:
        ollama.list()
    except Exception:
        print("Starting Ollama...")
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(4)


def describe_image(image_path: str, model: str = "moondream") -> str:
    ensure_ollama_running()

    available_models = [m.model for m in ollama.list().models]
    if not any(model in m for m in available_models):
        print(f"Pulling {model}...")
        ollama.pull(model)

    image_data = base64.b64encode(Path(image_path).read_bytes()).decode("utf-8")

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": "Describe this image in detail.", "images": [image_data]}]
    )

    return response.message.content.strip()


print(describe_image("images/pyramids_of_giza.png"))