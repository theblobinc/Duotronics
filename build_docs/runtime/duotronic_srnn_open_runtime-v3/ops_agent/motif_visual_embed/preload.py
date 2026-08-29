from pathlib import Path
from transformers import AutoImageProcessor, AutoModel
MODEL_ID="facebook/dinov2-small"
DEST=Path("/opt/models/dinov2-small")
DEST.mkdir(parents=True,exist_ok=True)
processor=AutoImageProcessor.from_pretrained(MODEL_ID)
model=AutoModel.from_pretrained(MODEL_ID)
processor.save_pretrained(DEST)
model.save_pretrained(DEST,safe_serialization=True)
print("PRELOADED",MODEL_ID,DEST)
