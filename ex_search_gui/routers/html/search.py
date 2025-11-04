import uuid
import json
import re

from fastapi import APIRouter, Request, Depends, Form, status, HTTPException, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from databases.sql.search.repository import SearchURLConfigRepositorySQL
from domain.models.search import command as search_command

from databases.sql.util import get_async_session
from app.label import SearchLabelViewTemplageService
from domain.schemas.search.search import (
    SearchResult,
    SearchURLConfigSchema,
    SearchURLConfigPreviewRequest,
)
from domain.schemas.search.html import SearchLabelAddForm, SearchLabelPreviewContext

router = APIRouter(prefix="/search", tags=["search"])
templates = Jinja2Templates(directory="templates")

CALLER_TYPE = "html.search"


@router.get("/labels/", response_class=HTMLResponse)
async def read_labels(
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
    log.info("html labels called", label=label)
    service = SearchLabelViewTemplageService(db_session=db, label=label)
    labels = await service.execute(label=label)
    context = labels.model_dump() | {"label": label}
    return templates.TemplateResponse(
        request=request, name="search/label_view.html", context=context
    )


@router.get("/labels/add/", response_class=HTMLResponse)
async def read_labels_add(
    request: Request,
):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("html labels add called")
    # download_type の選択肢をモデル定義から取得
    download_type_options = SearchURLConfigSchema.model_fields[
        "download_type"
    ].annotation.__args__
    context = {"download_type_options": download_type_options}
    return templates.TemplateResponse(
        request=request, name="search/label_add.html", context=context
    )


@router.post("/labels/add/confirm/", response_class=HTMLResponse)
async def read_labels_add_confirm(
    request: Request,
    label_name: str = Form(...),  # 直接Form依存関係を使用
    base_url: str = Form(...),
    query: str = Form(...),
    query_encoding: str = Form("utf-8"),
    download_type: str = Form(""),
    download_config: str = Form(""),
):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    form_data = SearchLabelAddForm(
        label_name=label_name,
        base_url=base_url,
        query=query,
        query_encoding=query_encoding,
        download_type=download_type,
        download_config=download_config,
    )
    log.info("html labels add confirm called", form_data=form_data)

    # JSON文字列を辞書に変換
    try:
        pattern = r",(\s*[}\]])"
        # 置換処理
        cleaned_json_str = re.sub(pattern, r"\1", form_data.download_config)
        download_config_dict = json.loads(cleaned_json_str)
    except json.JSONDecodeError:
        download_config_dict = {}

    preview = SearchURLConfigPreviewRequest(
        **form_data.model_dump(exclude={"download_config"}),
        download_config=download_config_dict
    )
    context = SearchLabelPreviewContext(
        preview=preview, is_edit_mode=False
    ).model_dump()

    return templates.TemplateResponse(
        request=request, name="search/label_confirm.html", context=context
    )


@router.post("/labels/{label_id}/edit/", response_class=HTMLResponse)
async def edit_label(
    request: Request,
    label_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("html label edit called", label_id=label_id)

    repo = SearchURLConfigRepositorySQL(db)
    config = await repo.get_all(search_command.SearchURLConfigCommand(id=label_id))
    if not config:
        raise HTTPException(status_code=404, detail="Label not found")
    if len(config) > 1:
        raise HTTPException(status_code=500, detail="Multiple labels found")
    config = config[0]

    # DBモデルをPydanticスキーマに変換
    preview = SearchURLConfigPreviewRequest.model_validate(config.model_dump())

    context = SearchLabelPreviewContext(preview=preview, is_edit_mode=True).model_dump()

    return templates.TemplateResponse(
        request=request, name="search/label_confirm.html", context=context
    )
