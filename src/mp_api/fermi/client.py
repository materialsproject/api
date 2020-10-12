from mp_api.core.client import BaseRester, MPRestError


class FermiRester(BaseRester):

    suffix = "fermi"

    def get_fermi_surface_from_material_id(self, material_id: str):
        """
        Get fermi surface data for a given Materials Project ID.

        Arguments:
            material_id (str): Materials project ID

        Returns:
            results (Dict): Dictionary containing fermi surface data.
        """

        result = self._make_request("{}/?all_fields=true".format(material_id))

        if len(result.get("data", [])) > 0:
            return result
        else:
            raise MPRestError("No document found")
