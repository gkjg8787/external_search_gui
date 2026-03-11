import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from databases.sql.util import get_async_session
from domain.models.search import command as search_command, search as search_model
from domain.schemas import search as search_schema
from databases.sql.search.repository import (
    SearchURLConfigRepositorySQL as urlconfig_repo,
    ProductPageConfigRepositorySQL as productconfig_repo,
    GroupRepository,
)
from app.search.search_api import (
    search_via_api_for_preview,
    get_product_via_api_for_preview,
    generate_download_config_via_api,
)
from app.label.add import SearchLabelDownLoadConfigTemplateService
from app.label.create import create_labels

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/labels/", response_model=list[search_schema.SearchLabelResponse])
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
            search_schema.SearchLabelResponse(
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


@router.post("/labels/", response_model=search_schema.SearchURLConfigResponse)
async def post_labels(
    request: Request,
    labelreq: search_schema.SearchURLConfigRequest,
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
    return search_schema.SearchURLConfigResponse(success=True)


@router.put("/labels/{id}/", response_model=search_schema.SearchURLConfigResponse)
async def update_label(
    request: Request,
    id: int,
    labelreq: search_schema.SearchURLConfigRequest,
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
    return search_schema.SearchURLConfigResponse(success=True)


@router.post(
    "/labels/preview/", response_model=search_schema.SearchURLConfigPreviewResponse
)
async def post_labels_preview(
    request: Request,
    previewreq: search_schema.SearchURLConfigPreviewRequest,
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


@router.delete("/labels/{id}/", response_model=search_schema.SearchURLConfigResponse)
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
    return search_schema.SearchURLConfigResponse(success=True)


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


@router.post("/labels/search/", response_model=search_schema.SearchByLabelResponse)
async def search_by_label(
    request: Request,
    searchreq: search_schema.SearchByLabelRequest,
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
    preview_request = search_schema.SearchURLConfigPreviewRequest(
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
        return search_schema.SearchByLabelResponse(results={})
    # response.resultsはURLをキーとする辞書なので、最初の値を取得する
    first_result = list(response.results.values())[0]
    return search_schema.SearchByLabelResponse(
        results={searchreq.label_id: first_result}
    )


@router.post(
    "/labels/product/preview/",
    response_model=search_schema.ProductPageConfigPreviewResponse,
)
async def post_product_page_config_preview(
    request: Request,
    previewreq: search_schema.ProductPageConfigPreviewRequest,
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


@router.get("/labels/product/", response_model=list[search_schema.ProductLabelResponse])
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
            search_schema.ProductLabelResponse(
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


@router.post("/labels/product/", response_model=search_schema.ProductPageConfigResponse)
async def post_product_page_label(
    request: Request,
    labelreq: search_schema.ProductPageConfigRequest,
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
    return search_schema.ProductPageConfigResponse(success=True)


@router.put(
    "/labels/product/{id}/", response_model=search_schema.ProductPageConfigResponse
)
async def update_product_page_label(
    request: Request,
    id: int,
    labelreq: search_schema.ProductPageConfigRequest,
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
    return search_schema.ProductPageConfigResponse(success=True)


@router.delete(
    "/labels/product/{id}/", response_model=search_schema.ProductPageConfigResponse
)
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
    return search_schema.ProductPageConfigResponse(success=True)


# --- Group CRUD ---


@router.get("/groups/", response_model=list[search_schema.GroupResponse])
async def get_all_groups(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
):
    """グループ一覧の取得"""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("api get all groups called")
    repo = GroupRepository(db)
    db_groups = await repo.get_all_groups()
    if db_groups:
        groups = [
            search_schema.GroupResponse(
                id=db_group.id,
                name=db_group.name,
            )
            for db_group in db_groups
        ]
    else:
        groups = []
    return groups


@router.get(
    "/groups/{group_id}/labels/", response_model=list[search_schema.SearchLabelResponse]
)
async def get_labels_for_group(
    request: Request,
    group_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    """グループ指定から所属するラベル(SearchURLConfig)の一覧の取得"""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("api get labels for group called", group_id=group_id)
    repo = GroupRepository(db)
    db_labels = await repo.get_labels_for_group(group_id)
    if db_labels:
        labels = [
            search_schema.SearchLabelResponse(
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


@router.post("/groups/", response_model=search_schema.GroupResponse, status_code=201)
async def create_group(
    request: Request,
    group_create: search_schema.GroupCreate,
    db: AsyncSession = Depends(get_async_session),
):
    """グループの新規作成"""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("api create group called", group_name=group_create.name)
    repo = GroupRepository(db)
    group = search_model.Group(name=group_create.name)
    db_created_group = await repo.create_group(group)
    if db_created_group is None:
        raise HTTPException(status_code=500, detail="Failed to create group")
    created_group = search_schema.GroupResponse(
        id=db_created_group.id,
        name=db_created_group.name,
    )
    return created_group


@router.put("/groups/{group_id}/", response_model=search_schema.GroupResponse)
async def update_group_name(
    request: Request,
    group_id: int,
    group_update: search_schema.GroupUpdate,
    db: AsyncSession = Depends(get_async_session),
):
    """グループ名の更新"""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info(
        "api update group name called", group_id=group_id, new_name=group_update.name
    )
    repo = GroupRepository(db)
    db_updated_group = await repo.update_group_name(group_id, group_update.name)
    if not db_updated_group:
        raise HTTPException(status_code=404, detail="Group not found")
    updated_group = search_schema.GroupResponse(
        id=db_updated_group.id,
        name=db_updated_group.name,
    )
    return updated_group


@router.delete(
    "/groups/{group_id}/", response_model=search_schema.GeneralSuccessResponse
)
async def delete_group(
    request: Request,
    group_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    """グループの削除"""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("api delete group called", group_id=group_id)
    repo = GroupRepository(db)
    success = await repo.delete_group(group_id)
    if not success:
        raise HTTPException(status_code=404, detail="Group not found")
    return search_schema.GeneralSuccessResponse(success=True)


@router.post(
    "/groups/{group_id}/labels/{label_id}/",
    response_model=search_schema.GeneralSuccessResponse,
    status_code=201,
)
async def add_label_to_group(
    request: Request,
    group_id: int,
    label_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    """指定グループに指定ラベル(SearchURLConfig)を所属させる"""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("api add label to group called", group_id=group_id, label_id=label_id)
    repo = GroupRepository(db)
    link = await repo.add_label_to_group(group_id, label_id)
    if not link:
        # 既に存在する場合や、親が見つからない場合など。
        # Repositoryの実装によってはより詳細なエラーハンドリングが必要。
        raise HTTPException(status_code=400, detail="Could not add label to group")
    return search_schema.GeneralSuccessResponse(success=True)


@router.delete(
    "/groups/{group_id}/labels/{label_id}/",
    response_model=search_schema.GeneralSuccessResponse,
)
async def remove_label_from_group(
    request: Request,
    group_id: int,
    label_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    """指定グループから指定ラベル(SearchURLConfig)を外す"""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("api remove label from group called", group_id=group_id, label_id=label_id)
    repo = GroupRepository(db)
    success = await repo.remove_label_from_group(group_id, label_id)
    if not success:
        raise HTTPException(status_code=404, detail="Link not found")
    return search_schema.GeneralSuccessResponse(success=True)


@router.post(
    "/downloadconfig/generate/",
    response_model=search_schema.DownloadConfigGenerateResponse,
)
async def post_download_config_generate(
    request: Request,
    downloadconfigreq: search_schema.DownloadConfigGenerateRequest,
    db: AsyncSession = Depends(get_async_session),
):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("api download config generate called", downloadconfigreq=downloadconfigreq)
    ok, result = await generate_download_config_via_api(db, downloadconfigreq)
    if not ok:
        raise HTTPException(status_code=400, detail=result)
    return result


@router.post(
    "/labels/generate_from_url",
    response_model=list[search_schema.SearchLabelResponse],
)
async def generate_labels_from_url(
    request: Request,
    req: search_schema.GenerateLabelsRequest,
    ses: AsyncSession = Depends(get_async_session),
):
    """
    URLから検索ラベル設定を生成する
    """
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("api generate labels from url called", req=req)
    try:
        # create_labelsはDBモデルのリストを返す
        generated_labels = await create_labels(ses, req.url, req.search_keyword)
        # FastAPIが自動的にPydanticスキーマに変換してレスポンスを生成する
        return generated_labels
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 予期せぬエラー
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/labels/batch", response_model=dict)
async def post_labels_batch(
    request: Request,
    labels: list[search_schema.SearchURLConfigRequest] = Body(...),
    ses: AsyncSession = Depends(get_async_session),
):
    """
    複数のラベル設定を一括でDBに登録する
    """
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        router_path=request.url.path,
        request_id=str(uuid.uuid4()),
    )
    log = structlog.get_logger(__name__)
    log.info("api labels batch called", labels=labels)
    if not labels:
        raise HTTPException(status_code=400, detail="No labels provided.")
    try:
        # PydanticスキーマからDBモデルに変換
        db_labels = [
            search_model.SearchURLConfig(**label.model_dump(exclude_unset=True))
            for label in labels
        ]
        repo = urlconfig_repo(ses)
        await repo.save_all(db_labels)
        return {
            "success": True,
            "message": f"{len(db_labels)} labels have been registered.",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to register labels: {str(e)}"
        )
