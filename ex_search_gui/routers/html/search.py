import uuid
import json
import re
from urllib.parse import urlencode, urlparse

from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, status, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from databases.sql.search.repository import (
    SearchURLConfigRepositorySQL,
    ProductPageConfigRepositorySQL,
    GroupRepository,
)
from domain.models.search import command as search_command
from databases.sql.util import get_async_session
from app.label import SearchLabelViewTemplateService, ProductPageLabelMatchService
from app.s2k import utils as s2k_utils
from common.read_config import get_html_options
from domain.schemas.search.search import (
    SearchURLConfigSchema,
    SearchURLConfigPreviewRequest,
    ProductPageConfig,
    ProductPageConfigPreviewRequest,
)
from domain.schemas.search.html import (
    SearchLabelAddForm,
    SearchLabelPreviewContext,
    ProductPageLabelPreviewContext,
)
from common import read_template

router = APIRouter(prefix="/search", tags=["search"])
templates = read_template.templates

CALLER_TYPE = "html.search"


@router.get("/", response_class=HTMLResponse)
async def read_search(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    group_id: str = Query(default=""),
):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("html search called", group_id=group_id)

    # グループ一覧を取得
    group_repo = GroupRepository(db)
    groups = await group_repo.get_all_groups()

    # ラベル一覧を取得
    labels_repo = SearchURLConfigRepositorySQL(db)
    try:
        group_id_int = int(group_id)
    except ValueError:
        group_id_int = None
    if group_id_int:
        # グループが選択されている場合は、そのグループに所属するラベルを取得
        labels = await group_repo.get_labels_for_group(group_id_int)
    else:
        # グループが選択されていない場合は、すべてのラベルを取得
        labels = await labels_repo.get_all(search_command.SearchURLConfigCommand())

    context = {"groups": groups, "labels": labels, "selected_group_id": group_id_int}

    html_opts = get_html_options()

    try:
        show_registration = bool(html_opts.search2kakaku.registration)
    except Exception:
        show_registration = False
    context["show_registration"] = show_registration

    try:
        if html_opts.kakakuscraping.enabled:
            context["kakakuscraping"] = {
                "url": html_opts.kakakuscraping.url,
                "enalbled": True,
            }
    except Exception:
        context["kakakuscraping"] = {"enabled": False}

    return templates.TemplateResponse(
        request=request,
        name="search/label_search.html",
        context=context,
    )


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
    service = SearchLabelViewTemplateService(db_session=db, label=label)
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
        log.warning(
            "Invalid JSON in download_config", download_config=form_data.download_config
        )
        download_config_dict = {}
    if not download_config_dict:
        download_config_dict = {
            "sitename": "example_sitename",
            "label": "example_label",
        }

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


@router.get("/labels/product/", response_class=HTMLResponse)
async def read_product_labels(
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
    log.info("html product labels called", label=label)

    repo = ProductPageConfigRepositorySQL(db)
    command = search_command.ProductPageConfigCommand(label_name=label)
    configs = await repo.get_all(command)

    context = {"labels": configs, "label": label}
    return templates.TemplateResponse(
        request=request, name="search/product_label_view.html", context=context
    )


@router.get("/labels/product/add/", response_class=HTMLResponse)
async def read_product_labels_add(
    request: Request,
):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("html product labels add called")

    # モデル定義から選択肢を取得
    pattern_type_options = ProductPageConfig.model_fields[
        "pattern_type"
    ].annotation.__args__
    download_type_options = ProductPageConfig.model_fields[
        "download_type"
    ].annotation.__args__

    context = {
        "pattern_type_options": pattern_type_options,
        "download_type_options": download_type_options,
    }
    return templates.TemplateResponse(
        request=request, name="search/product_label_add.html", context=context
    )


@router.post("/labels/product/add/confirm/", response_class=HTMLResponse)
async def read_product_labels_add_confirm(
    request: Request,
    label_name: str = Form(...),
    url_pattern: str = Form(...),
    pattern_type: str = Form(""),
    download_type: str = Form(""),
    download_config: str = Form(""),
):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)

    form_data = {
        "label_name": label_name,
        "url_pattern": url_pattern,
        "pattern_type": pattern_type,
        "download_type": download_type,
    }
    log.info("html product labels add confirm called", form_data=form_data)

    try:
        pattern = r",(\s*[}\]])"
        cleaned_json_str = re.sub(pattern, r"\1", download_config)
        download_config_dict = json.loads(cleaned_json_str) if cleaned_json_str else {}
    except json.JSONDecodeError:
        log.warning("Invalid JSON in download_config", download_config=download_config)
        download_config_dict = {}

    if not download_config_dict:
        download_config_dict = {
            "sitename": "example_sitename",
            "label": "example_label",
        }

    preview = ProductPageConfigPreviewRequest(
        label_name=label_name,
        url_pattern=url_pattern,
        pattern_type=pattern_type,
        download_type=download_type,
        download_config=download_config_dict,
    )

    context = ProductPageLabelPreviewContext(
        preview=preview, is_edit_mode=False
    ).model_dump()

    return templates.TemplateResponse(
        request=request, name="search/product_label_confirm.html", context=context
    )


@router.post("/labels/product/{label_id}/edit/", response_class=HTMLResponse)
async def edit_product_label(
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
    log.info("html product label edit called", label_id=label_id)

    repo = ProductPageConfigRepositorySQL(db)
    config = await repo.get_all(
        search_command.ProductPageConfigCommand(label_id=label_id)
    )
    if not config:
        raise HTTPException(status_code=404, detail="Product label not found")
    if len(config) > 1:
        raise HTTPException(status_code=500, detail="Multiple Product labels found")
    config = config[0]

    # DBモデルをPydanticスキーマに変換
    preview = ProductPageConfigPreviewRequest.model_validate(config.model_dump())

    context = ProductPageLabelPreviewContext(
        preview=preview, is_edit_mode=False
    ).model_dump()

    return templates.TemplateResponse(
        request=request, name="search/product_label_confirm.html", context=context
    )


# 登録確認ページ (ウォッチ登録) を受け取り表示する
@router.post("/product/", response_class=HTMLResponse)
async def post_product_watch(
    request: Request,
    subURL: str = Form(...),
    db: AsyncSession = Depends(get_async_session),
):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("html product watch called", subURL=subURL)
    db_config = await ProductPageLabelMatchService(db_session=db, url=subURL).execute()
    log.info("ProductPageLabelMatchService called", db_config=db_config)
    # モデル定義から選択肢を取得
    pattern_type_options = ProductPageConfig.model_fields[
        "pattern_type"
    ].annotation.__args__
    download_type_options = ProductPageConfig.model_fields[
        "download_type"
    ].annotation.__args__

    context = {
        "subURL": subURL,
        "pattern_type_options": pattern_type_options,
        "download_type_options": download_type_options,
        "db_config": db_config.model_dump() if db_config else None,
    }

    return templates.TemplateResponse(
        request=request, name="search/product_watch_confirm.html", context=context
    )


@router.post("/product-watch/confirm-label", response_class=HTMLResponse)
async def confirm_product_label_creation(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    url: str = Form(...),
    label_name: str = Form(...),
    pattern_type: str = Form(...),
    url_pattern: str = Form(...),
    download_type: str = Form(...),
    options: str = Form(...),
    sitename: str = Form(...),
):
    """商品ページラベルの作成を確認するページを表示する"""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("confirm product label creation called", label_name=label_name)

    repo = ProductPageConfigRepositorySQL(db)
    existing_label = await repo.get_all(
        search_command.ProductPageConfigCommand(label_name=label_name)
    )

    form_data = {
        "url": url,
        "label_name": label_name,
        "pattern_type": pattern_type,
        "url_pattern": url_pattern,
        "download_type": download_type,
        "options": options,
        "sitename": sitename,
    }

    if existing_label:
        method = s2k_utils.get_url_method("url_add")
        if method.lower() != "get":
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail="Method not allowed for existing label redirection",
            )
        # ラベルが既に存在する場合、既存のウォッチ登録処理へリダイレクト
        log.info("Label already exists. Redirecting to post_product_watch.")
        base_path = s2k_utils.get_url_link("url_add")
        query_params = {
            "url": url,
            "sitename": sitename,
            "options": options,
        }
        encoded_query = urlencode(query_params)
        redirect_url = urlparse(base_path)._replace(query=encoded_query).geturl()

        return RedirectResponse(url=redirect_url, status_code=303)

    # ラベルが存在しない場合、作成確認ページを表示
    log.info("Label does not exist. Showing creation confirmation page.")
    return templates.TemplateResponse(
        "search/product_label_creation_confirm.html",
        {
            "request": request,
            "form_data": form_data,
            "add_label_action": request.url_for("read_product_labels_add_confirm"),
            "watch_only_action": s2k_utils.get_url_link("url_add"),
            "watch_only_method": s2k_utils.get_url_method("url_add"),
        },
    )
