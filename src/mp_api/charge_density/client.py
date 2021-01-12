from mp_api.core.client import BaseRester, MPRestError
from mp_api.tasks.client import TaskRester


class ChargeDensityRester(BaseRester):

    suffix = "charge_density"

    def get_charge_density_from_material_id(self, material_id: str):
        """
        Get charge density data for a given Materials Project ID.

        Arguments:
            material_id (str): Materials project ID

        Returns:
            chgcar (dict): Pymatgen CHGCAR object.
        """

        result = self._make_request(
            "{}/?fields=data&all_fields=false".format(material_id)
        )

        if result.get("data", None) is not None:
            return result["data"]
        else:
            raise MPRestError("No document found")

    def get_calculation_details(self, material_id: str):
        """
        Get charge density calculations details for a given Materials Project ID.

        Arguments:
            material_id (str): Materials project ID

        Returns:
            calc_details (dict): Dictionary containing INCAR, POSCAR, and KPOINTS data for the DFT calculation.
        """

        base_endpoint = "/".join(self.endpoint.split("/")[0:3])
        task_rester = TaskRester(api_key=self.api_key, endpoint=base_endpoint)

        result = task_rester.get_task_from_material_id(
            material_id, fields=["task_id", "orig_inputs"]
        ).get("data")[0]

        task_rester.session.close()

        return result
