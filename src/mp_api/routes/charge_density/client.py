from mp_api.core.client import BaseRester, MPRestError
from mp_api.routes.tasks.client import TaskRester
from mp_api.routes.materials.client import MaterialsRester


class ChargeDensityRester(BaseRester):

    suffix = "charge_density"

    def get_charge_density_from_calculation_id(self, task_id: str):
        """
        Get charge density data for a given calculation ID.

        Arguments:
            task_id (str): Calculation ID

        Returns:
            chgcar (dict): Pymatgen CHGCAR object.
        """

        result = self.get_document_by_id(document_id=task_id)

        if result.get("data", None) is not None:
            return result["data"]
        else:
            raise MPRestError("No charge density found")

    def get_calculation_details(self, task_id: str):
        """
        Get charge density calculations details for a given calculation ID.

        Arguments:
            task_id (str): Calculation ID

        Returns:
            calc_details (dict): Dictionary containing INCAR, POSCAR, and KPOINTS data for the DFT calculation.
        """

        task_rester = TaskRester(endpoint=self.base_endpoint, api_key=self.api_key)  # type: ignore

        result = task_rester.get_document_by_id(
            document_id=task_id,
            fields=["orig_inputs.incar", "orig_inputs.poscar", "orig_inputs.kpoints"],
        ).orig_inputs

        return result

    def get_calculation_ids_from_material_id(self, material_id: str):
        """
        Get charge density calculation ids associated with a given Materials Project ID
        that have charge density data.

        Arguments:
            material_id (str): Materials Project ID

        Returns:
            calculation_ids (List[str]): List of calculation ids that have charge density data.
        """

        materials_rester = MaterialsRester(  # type: ignore
            endpoint=self.base_endpoint, api_key=self.api_key
        )

        calculation_types = materials_rester.get_document_by_id(
            document_id=material_id, fields=["calc_types"]
        ).calc_types

        calculation_ids = []
        for calculation_id, calculation_type in calculation_types.items():
            if "Static" in calculation_type:
                calculation_ids.append(calculation_id)

        chgcar_calculation_ids = []
        for calculation_id in calculation_ids:
            try:
                result = self.get_document_by_id(
                    document_id=calculation_id, fields=["task_id"]
                )
            except MPRestError:
                continue

            chgcar_calculation_ids.append(result["task_id"])

        return chgcar_calculation_ids
