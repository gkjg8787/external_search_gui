from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASES = {
    "sync": {
        "drivername": "sqlite",
        "database": f"{BASE_DIR}/db/database.db",
    },
    "a_sync": {
        "drivername": "sqlite+aiosqlite",
        "database": f"{BASE_DIR}/db/database.db",
    },
}
LOG_OPTIONS = {"directory_path": f"{BASE_DIR}/log/"}
API_OPTIONS = {
    "get_data": {
        "url": "http://localhost:8060/api/",
        "timeout": 15.0,
        "sofmap": {"timeout": 17.0},
        "geo": {"timeout": 18.0},
        "gemini": {"timeout": 300.0},
    },
    "url_analysis": {"url": "http://localhost:8090/", "timeout": 60},
    "url_generate": {"url": "http://localhost:8090/", "timeout": 5},
}
HTML_OPTIONS = {
    "search2kakaku": {
        "registration": False,
        "url": "http://localhost:8120/",
    },
    "kakakuscraping": {
        "enabled": False,
        "url": "http://localhost:8000/",
    },
}
SEARCH_LABEL_RULES = {
    "PC": ["pc", "パソコン", "モニタ"],
    "食品・飲料": ["食品", "菓子", "飲料", "ドリンク", "酒"],
}
