from fastapi import APIRouter, HTTPException
from .models import InferenceLogPayload
from .database import insert_inference_log

router = APIRouter()


@router.post("/ingest/log")
async def ingest_log(payload: InferenceLogPayload):
    try:
        payload_dict = payload.model_dump(mode="json")
        row = insert_inference_log(payload_dict)
        return {"status": "ok", "id": row.get("id")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "ingestion"}
