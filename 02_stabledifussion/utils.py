from huggingface_hub import snapshot_download
from pathlib import Path
from PIL import Image
from io import BytesIO
import base64
import shutil

def download_model(model_name, local_model_path):
    local_model_path = Path(local_model_path)
    local_model_path.mkdir(exist_ok=True)
    local_cache_path = Path("./tmp_cache")
    snapshot_download(
        repo_id=model_name,
        local_dir_use_symlinks=False,
        revision="fp16",
        cache_dir=local_cache_path,
        local_dir=local_model_path,
        ignore_patterns=["*.ckpt", "*.safetensors"],
    )
    shutil.rmtree(local_cache_path)

    return local_model_path

def encode_image(image):
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    img_str = base64.b64encode(buffer.getvalue())

    return img_str


def decode_image(img):
    buff = BytesIO(base64.b64decode(img.encode("utf8")))
    image = Image.open(buff)
    return image