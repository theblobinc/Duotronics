import base64, hashlib, io, os
from typing import List
import numpy as np
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from PIL import Image
from transformers import AutoImageProcessor, AutoModel

MODEL_PATH="/opt/models/dinov2-small"
MODEL_NAME="facebook/dinov2-small"
THREADS=max(1,min(int(os.getenv("XAVI_EMBED_THREADS","32")), os.cpu_count() or 1))
torch.set_num_threads(THREADS)
torch.set_num_interop_threads(max(1,min(4,THREADS)))
processor=AutoImageProcessor.from_pretrained(MODEL_PATH,local_files_only=True)
model=AutoModel.from_pretrained(MODEL_PATH,local_files_only=True)
model.eval()
app=FastAPI(title="Xavi DINOv2 Visual Embedding Worker",version="1.0.0")

class BatchRequest(BaseModel):
    images_b64: List[str]=Field(min_length=1,max_length=32)
    normalize: bool=True
class SingleRequest(BaseModel):
    image_b64: str
    normalize: bool=True

def digest(raw: bytes)->str:
    token=base64.urlsafe_b64encode(hashlib.shake_256(raw).digest(64)).decode("ascii").rstrip("=")
    return "duoid:shake256-512:"+token

def decode_image(value: str):
    try:
        if "," in value and value.split(",",1)[0].startswith("data:"):
            value=value.split(",",1)[1]
        raw=base64.b64decode(value,validate=True)
        if not raw or len(raw)>8*1024*1024:
            raise ValueError("image size")
        image=Image.open(io.BytesIO(raw)).convert("RGB")
        return raw,image
    except Exception as exc:
        raise HTTPException(status_code=422,detail="invalid_image_b64") from exc

def embed(values: List[str], normalize: bool):
    decoded=[decode_image(v) for v in values]
    raws=[x[0] for x in decoded]
    images=[x[1] for x in decoded]
    inputs=processor(images=images,return_tensors="pt")
    with torch.inference_mode():
        vectors=model(**inputs).last_hidden_state[:,0,:].float()
        if normalize:
            vectors=torch.nn.functional.normalize(vectors,p=2,dim=1)
    arr=vectors.cpu().numpy().astype(np.float32)
    return [{"input_digest":digest(raw),"embedding":[round(float(v),8) for v in vec.tolist()],"dimensions":int(vec.shape[0])}
            for raw,vec in zip(raws,arr)]

@app.get("/health")
def health():
    return {"status":"ok","schema_version":"xavi-visual-embedding-worker/v1","model":MODEL_NAME,
            "dimensions":384,"device":"cpu","threads":THREADS,"normalized_default":True,
            "internet_required":False,"authority":"perceptual_embedding_similarity_evidence_only",
            "identity_semantics":"not_person_identity_evidence; visual appearance/composition/content similarity only"}

@app.post("/embed")
def embed_single(req: SingleRequest):
    item=embed([req.image_b64],req.normalize)[0]
    return {"schema_version":"xavi-visual-embedding/v1","model":MODEL_NAME,"normalized":req.normalize,**item,
            "authority":"perceptual_embedding_similarity_evidence_only","identity_semantics":"not_person_identity_evidence"}

@app.post("/embed/batch")
def embed_batch(req: BatchRequest):
    items=embed(req.images_b64,req.normalize)
    return {"schema_version":"xavi-visual-embedding-batch/v1","model":MODEL_NAME,"normalized":req.normalize,
            "count":len(items),"items":items,"authority":"perceptual_embedding_similarity_evidence_only",
            "identity_semantics":"not_person_identity_evidence"}
