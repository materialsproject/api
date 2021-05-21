from mp_api.core.client import BaseRester
from mp_api.routes.wulff.models import WulffDoc


class WulffRester(BaseRester):

    suffix = "wulff"
    document_model = WulffDoc  # type: ignore
    primary_key = "task_id"
