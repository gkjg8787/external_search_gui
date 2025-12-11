from urllib.parse import urljoin

from common.read_config import get_html_options

HTMLLINKCONFIG = {
    "url": {"root_path" "/url/"},
    "url_add": {"root_path": "/url/add/", "method": "get"},
}


def get_url_link(path_name: str = "url"):
    opts = get_html_options()
    return urljoin(opts.search2kakaku.url, HTMLLINKCONFIG[path_name]["root_path"])


def get_url_method(path_name: str = "url"):
    return HTMLLINKCONFIG[path_name].get("method", "post")
