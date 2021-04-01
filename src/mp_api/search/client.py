from mp_api.core.client import BaseRester
from mp_api.search.models import SearchDoc

class SearchRester(BaseRester):
    suffix = "search"
    document_model = SearchDoc