from mp_api.core.client import BaseRester, MPRestError
from mp_api.dois.models import DOIDoc


class DOIRester(BaseRester):

    suffix = "doi"
    document_model = DOIDoc

    def get_eos_from_material_id(self, material_id: str):
        """
        Get DOI and reference data for a given Materials Project ID.

        Arguments:
            material_id (str): Materials project ID

        Returns:
            results (Dict): Dictionary containing DOI and reference data of state data.
        """

        result = self._make_request("{}/?all_fields=true".format(material_id))

        if len(result.get("data", [])) > 0:
            return result
        else:
            raise MPRestError("No document found")
