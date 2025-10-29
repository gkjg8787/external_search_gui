from .constants import API_OPTIONS
from .models.apioption import APIPathOption
from .enums import APIURLName


class APIPathOptionFactory:
    def create(self, apiurlname: APIURLName):
        name = apiurlname.name.lower()
        return APIPathOption(name=name, **API_OPTIONS[name])
