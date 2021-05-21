from mp_api.core.client import BaseRester


class SimilarityRester(BaseRester):

    suffix = "similarity"
    primary_key = "task_id"
