"""api/routes/linkask.py - Endpoint POST linkask."""
import logging
import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_db
from api.models.link import LinkAskRequest, LinkAskResponse
from api.models.common import success_response
from api.services.report_service import ask_link


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/share", tags=["linkask"])


@router.post(
    "/linkask/{slug}",
    summary="Cek ketersediaan link",
    description="Cek apakah anime punya link stream/download di DB.",
)
async def post_linkask_endpoint(
    slug: str,
    body: LinkAskRequest = None,
    db: Session = Depends(get_db),
):
    t0 = time.time()

    if body is None:
        body = LinkAskRequest()

    result = ask_link(
        db,
        slug=slug,
        type_=body.type,
        deep=body.deep,
    )

    data = LinkAskResponse(**result)

    duration_ms = int((time.time() - t0) * 1000)
    return success_response(
        data=data.model_dump(),
        cached=True,
        source="db",
        duration_ms=duration_ms,
    )
