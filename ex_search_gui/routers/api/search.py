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
    SearchByLabelRequest,
    SearchByLabelResponse,
    ProductPageConfigPreviewRequest,
    ProductPageConfigPreviewResponse,
    ProductPageConfigRequest,
    ProductPageConfigResponse,
    ProductLabelResponse,
)
from databases.sql.search.repository import (
    SearchURLConfigRepositorySQL as urlconfig_repo,
    ProductPageConfigRepositorySQL as productconfig_repo,
)
from app.search.search_api import (
    search_via_api_for_preview,
    get_product_via_api_for_preview,
)
from app.label.add import SearchLabelDownLoadConfigTemplateService

router = APIRouter(prefix="/api", tags=["api"])


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
                id=db_label.id,
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


@router.put("/labels/{id}/", response_model=SearchURLConfigResponse)
async def update_label(
    request: Request,
    id: int,
    labelreq: SearchURLConfigRequest,
    db: AsyncSession = Depends(get_async_session),
):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("api label update called", id=id, labelreq=labelreq)

    # IDが一致していることを確認
    if labelreq.id != id:
        raise HTTPException(
            status_code=400, detail="Path ID does not match request body ID"
        )

    # SearchURLConfigRequestはidを含んでいるので、そのままモデルに変換できる
    urlconfig = search_model.SearchURLConfig.model_validate(labelreq)

    try:
        await urlconfig_repo(db).save_all([urlconfig])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
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
        await urlconfig_repo(db).delete_by_id(id)
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

    return config_template.model_dump(exclude_none=True)


@router.post("/labels/search/", response_model=SearchByLabelResponse)
async def search_by_label(
    request: Request,
    searchreq: SearchByLabelRequest,
    db: AsyncSession = Depends(get_async_session),
):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("api search by labels called", searchreq=searchreq)
    db_labels = await urlconfig_repo(db).get_all(
        command=search_command.SearchURLConfigCommand(id=searchreq.label_id)
    )
    if not db_labels:
        raise HTTPException(status_code=404, detail="Label not found")
    if len(db_labels) > 1:
        raise HTTPException(
            status_code=500, detail="Multiple labels found with the same ID"
        )
    db_label = db_labels[0]
    preview_request = SearchURLConfigPreviewRequest(
        id=db_label.id,
        label_name=db_label.label_name,
        base_url=db_label.base_url,
        query=db_label.query,
        query_encoding=db_label.query_encoding,
        download_type=db_label.download_type,
        download_config=db_label.download_config,
        keywords=[searchreq.keyword],
    )
    response = await search_via_api_for_preview(ses=db, searchreq=preview_request)
    if len(response.results) == 0:
        return SearchByLabelResponse(results={})
    # response.resultsはURLをキーとする辞書なので、最初の値を取得する
    first_result = list(response.results.values())[0]
    return SearchByLabelResponse(results={searchreq.label_id: first_result})


@router.post(
    "/labels/product/preview/", response_model=ProductPageConfigPreviewResponse
)
async def post_product_page_config_preview(
    request: Request,
    previewreq: ProductPageConfigPreviewRequest,
    db: AsyncSession = Depends(get_async_session),
):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("api product page config preview called", previewreq=previewreq)
    response = await get_product_via_api_for_preview(ses=db, productreq=previewreq)
    return response


@router.get("/labels/product/", response_model=list[ProductLabelResponse])
async def get_product_page_labels(
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
    log.info("api product page labels called", label=label)
    db_labels = await productconfig_repo(db).get_all(
        search_command.ProductPageConfigCommand(label_name=label)
    )
    if db_labels:
        labels = [
            ProductLabelResponse(
                id=db_label.id,
                label_name=db_label.label_name,
                url_pattern=db_label.url_pattern,
                pattern_type=db_label.pattern_type,
                download_type=db_label.download_type,
                download_config=db_label.download_config,
            )
            for db_label in db_labels
        ]
    else:
        labels = []
    return labels


@router.post("/labels/product/", response_model=ProductPageConfigResponse)
async def post_product_page_label(
    request: Request,
    labelreq: ProductPageConfigRequest,
    db: AsyncSession = Depends(get_async_session),
):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("api product page label post called", labelreq=labelreq)
    product_configs = [
        search_model.ProductPageConfig(
            label_name=labelreq.label_name,
            url_pattern=labelreq.url_pattern,
            pattern_type=labelreq.pattern_type,
            download_type=labelreq.download_type,
            download_config=labelreq.download_config,
        )
    ]
    await productconfig_repo(db).save_all(product_configs)
    return ProductPageConfigResponse(success=True)


@router.put("/labels/product/{id}/", response_model=ProductPageConfigResponse)
async def update_product_page_label(
    request: Request,
    id: int,
    labelreq: ProductPageConfigRequest,
    db: AsyncSession = Depends(get_async_session),
):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("api product page label update called", id=id, labelreq=labelreq)

    if labelreq.id != id:
        raise HTTPException(
            status_code=400, detail="Path ID does not match request body ID"
        )

    product_config = search_model.ProductPageConfig.model_validate(labelreq)

    try:
        await productconfig_repo(db).save_all([product_config])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ProductPageConfigResponse(success=True)


@router.delete("/labels/product/{id}/", response_model=ProductPageConfigResponse)
async def delete_product_page_label(
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
    log.info("api product page label delete called", id=id)
    try:
        await productconfig_repo(db).delete_by_id(id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ProductPageConfigResponse(success=True)
