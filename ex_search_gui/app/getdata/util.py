import os
from common.read_config import get_api_options
from .models.apioption import APIPathOption


def get_api_base_url():
    apisendopt = get_api_options()
    return apisendopt.get_data.url


def create_api_url(apiopt: APIPathOption):
    base_url = get_api_base_url()
    return os.path.join(base_url, apiopt.path)
