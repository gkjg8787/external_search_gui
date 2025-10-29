from pydantic import BaseModel


class APIPathOption(BaseModel):
    name: str
    path: str
    method: str
