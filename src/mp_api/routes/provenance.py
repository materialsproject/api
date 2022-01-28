from mp_api.core.client import BaseRester
from emmet.core.provenance import ProvenanceDoc


class ProvenanceRester(BaseRester[ProvenanceDoc]):

    suffix = "provenance"
    document_model = ProvenanceDoc  # type: ignore
    primary_key = "material_id"
