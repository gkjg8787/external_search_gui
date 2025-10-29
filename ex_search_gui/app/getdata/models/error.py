from pydantic import BaseModel


class ErrorMsg(BaseModel):
    detail: str
