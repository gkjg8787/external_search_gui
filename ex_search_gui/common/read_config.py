from pydantic import BaseModel, Field

import settings


class APISiteOption(BaseModel):
    timeout: float = Field(default=10.0)


class APIOtpion(BaseModel):
    url: str
    timeout: float = Field(default=5.0)
    gemini: APISiteOption | None = Field(default=None)


class APIOptions(BaseModel):
    get_data: APIOtpion
    post_data: APIOtpion


class SQLParams(BaseModel):
    drivername: str
    database: str
    username: str | None = None
    password: str | None = None
    host: str | None = None
    port: str | None = None


class DataBaseOptions(BaseModel):
    sync: SQLParams
    a_sync: SQLParams


class LogOptions(BaseModel):
    directory_path: str


def to_lower_keys(obj):
    if isinstance(obj, dict):
        # 新しい辞書を構築し、各キーを小文字に変換
        # 値が辞書の場合は再帰的にto_lower_keysを適用
        return {
            k.lower() if isinstance(k, str) else k: to_lower_keys(v)
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        # リストの場合は、各要素に対してto_lower_keysを適用
        return [to_lower_keys(elem) for elem in obj]
    else:
        # 辞書でもリストでもない場合はそのまま返す
        return obj


def get_api_options():
    lower_key_dict = to_lower_keys(settings.API_OPTIONS)
    return APIOptions(**lower_key_dict)


def get_databases():
    lower_key_dict = to_lower_keys(settings.DATABASES)
    return DataBaseOptions(**lower_key_dict)


def get_log_options():
    lower_key_dict = to_lower_keys(settings.LOG_OPTIONS)
    return LogOptions(**lower_key_dict)
