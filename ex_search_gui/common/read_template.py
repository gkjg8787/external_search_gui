import json

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


def custom_tojson_japanese(value, indent=None):
    """
    PythonオブジェクトをJSON文字列に変換し、
    日本語のエスケープを防ぎつつ、インデントを設定する。
    """
    # ensure_ascii=False で日本語のエスケープを防ぐ
    # indent=None の場合はインデントなし
    return json.dumps(value, ensure_ascii=False, indent=indent)


templates.env.filters["tojson_japanese"] = custom_tojson_japanese
