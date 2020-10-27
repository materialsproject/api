from mp_api.core.client import BaseRester, MPRestError


class PhononRester(BaseRester):

    suffix = "phonon"

    def get_phonon_from_material_id(self, material_id: str):
        """
        Get phonon band structure data for a given Materials Project ID.

        Arguments:
            material_id (str): Materials project ID

        Returns:
            results (Dict): Dictionary containing phonon band structure data.
        """

        result = self._make_request("{}/?all_fields=true".format(material_id))

        if len(result.get("data", [])) > 0:
            return result
        else:
            raise MPRestError("No document found")


class PhononImgRester(BaseRester):

    suffix = "phonon_img"

    def get_phonon_img_from_material_id(self, material_id: str):
        """
        Get phonon band structure image for a given Materials Project ID.

        Arguments:
            material_id (str): Materials project ID

        Returns:
            results (Dict): Dictionary containing phonon band structure image data.
        """

        result = self._make_request("{}/?all_fields=true".format(material_id))

        if len(result.get("data", [])) > 0:
            return result
        else:
            raise MPRestError("No document found")
