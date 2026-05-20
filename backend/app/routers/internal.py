from fastapi import APIRouter, Depends

from app.dependencies import verify_worker_token
from app.schemas import ClaimRequest, CompleteJobRequest, FailJobRequest, HeartbeatRequest
from app.services.ai_job_service import claim_jobs, complete_job, fail_job, heartbeat

router = APIRouter(prefix="/api/internal", tags=["internal"])


@router.post("/ai-workers/heartbeat", dependencies=[Depends(verify_worker_token)])
def worker_heartbeat(payload: HeartbeatRequest):
    return heartbeat(payload.worker_id, payload.status)


@router.post("/ai-jobs/claim", dependencies=[Depends(verify_worker_token)])
def claim(payload: ClaimRequest):
    return {"jobs": claim_jobs(payload.worker_id, payload.limit)}


@router.post("/ai-jobs/{job_id}/complete", dependencies=[Depends(verify_worker_token)])
def complete(job_id: int, payload: CompleteJobRequest):
    complete_job(job_id, payload.worker_id, payload.result)
    return {"job_id": job_id, "status": "completed"}


@router.post("/ai-jobs/{job_id}/fail", dependencies=[Depends(verify_worker_token)])
def fail(job_id: int, payload: FailJobRequest):
    fail_job(job_id, payload.worker_id, payload.error_message)
    return {"job_id": job_id, "status": "failed"}
