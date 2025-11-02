import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from databases.sql.util import get_async_session
from domain.models.search import command as search_command, search as search_model
from domain.schemas.search import (
    SearchLabelResponse,
    SearchURLConfigRequest,
    SearchURLConfigResponse,
    SearchURLConfigPreviewRequest,
    SearchURLConfigPreviewResponse,
)
from databases.sql.search.repository import (
    SearchURLConfigRepositorySQL as urlconfig_repo,
)
from app.search.search_api import search_via_api_for_preview
from app.label.add import SearchLabelDownLoadConfigTemplateService

router = APIRouter(prefix="/api", tags=["api"])

CALLER_TYPE = "api.search"


@router.get("/labels/", response_model=list[SearchLabelResponse])
async def get_labels(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    label: str | None = Query(default=None),
):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("api labels called", label=label)
    db_labels = await urlconfig_repo(db).get_all(
        search_command.SearchURLConfigCommand(label_name=label)
    )
    if db_labels:
        labels = [
            SearchLabelResponse(
                label_name=db_label.label_name,
                base_url=db_label.base_url,
                query=db_label.query,
                query_encoding=db_label.query_encoding,
                download_type=db_label.download_type,
                download_config=db_label.download_config,
            )
            for db_label in db_labels
        ]
    else:
        labels = []
    return labels


@router.post("/labels/", response_model=SearchURLConfigResponse)
async def post_labels(
    request: Request,
    labelreq: SearchURLConfigRequest,
    db: AsyncSession = Depends(get_async_session),
):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("api labels called", labelreq=labelreq)
    urlconfigs = [
        search_model.SearchURLConfig(
            label_name=labelreq.label_name,
            base_url=labelreq.base_url,
            query=labelreq.query,
            query_encoding=labelreq.query_encoding,
            download_type=labelreq.download_type,
            download_config=labelreq.download_config,
        )
    ]
    await urlconfig_repo(db).save_all(urlconfigs)
    return SearchURLConfigResponse(success=True)


@router.post("/labels/preview/", response_model=SearchURLConfigPreviewResponse)
async def post_labels_preview(
    request: Request,
    previewreq: SearchURLConfigPreviewRequest,
    db: AsyncSession = Depends(get_async_session),
):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("api labels preview called", previewreq=previewreq)
    response = await search_via_api_for_preview(ses=db, searchreq=previewreq)
    return response


@router.delete("/labels/{id}/", response_model=SearchURLConfigResponse)
async def delete_label(
    request: Request,
    id: int,
    db: AsyncSession = Depends(get_async_session),
):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("api label delete called", id=id)
    try:
        await urlconfig_repo(db).delte_by_id(id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"type:{type(e)}, value:{e}")
    return SearchURLConfigResponse(success=True)


@router.get("/labels/config/template/", response_model=dict)
async def get_label_config_template(
    request: Request,
    option_type: str = Query(
        ...,
        description="Type of download config template (e.g., 'nodriver', 'selenium')",
    ),
):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("api label config template called", option_type=option_type)

    service = SearchLabelDownLoadConfigTemplateService(option_type=option_type)
    config_template = await service.execute()

    if config_template is None:
        raise HTTPException(
            status_code=404, detail=f"No template found for option_type: {option_type}"
        )

    return config_template.model_dump()
