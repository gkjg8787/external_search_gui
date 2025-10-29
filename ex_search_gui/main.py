from contextlib import asynccontextmanager

from fastapi import FastAPI, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

# from routers.html import search
from routers.api import search
from databases.sql.create_table import create_table
from common.logger_config import configure_logger

configure_logger(filename="app.log", logging_level="INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_table()
    yield


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(search.router)


@app.get("/")
async def root(request: Request):
    return None
    # return RedirectResponse(
    #    url=request.url_for("read_admin_noticeloglist"),
    #    status_code=status.HTTP_302_FOUND,
    # )
