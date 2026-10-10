"""api/routes/reports.py - Endpoint POST report error."""
import logging
import time

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from api.deps import get_db
from api.models.report import ReportRequest, ReportResponse
from api.models.common import success_response
from api.services.report_service import report_error


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/share", tags=["reports"])


@router.post(
    "/errorid/{slug}",
    summary="Report link error",
    description="Kirim report link download/stream yang bermasalah.",
)
async def post_errorid_endpoint(
    slug: str,
    body: ReportRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    t0 = time.time()

    client_ip = request.client.host if request.client else ""

    report = report_error(
        db,
        slug=slug,
        url=body.url,
        reason=body.reason,
        quality=body.quality,
        host=body.host,
        reporter_ip=client_ip,
    )

    data = ReportResponse(
        id=report.id,
        slug=report.slug,
        type=report.type,
        url=report.url or None,
        reason=report.reason,
        resolved=report.resolved,
        created_at=report.created_at.isoformat() if report.created_at else None,
    )

    duration_ms = int((time.time() - t0) * 1000)
    return success_response(
        data=data.model_dump(),
        cached=False,
        source="db",
        duration_ms=duration_ms,
    )
