from platform import version
from mp_api.core.client import BaseRester, MPRestError
from mp_api.routes.tasks.client import TaskRester
from mp_api.routes.materials.client import MaterialsRester


class ChargeDensityRester(BaseRester):

    suffix = "charge_density"
    primary_key = "task_id"

    def get_charge_density_from_calculation_id(self, task_id: str):
        """
        Get charge density data for a given calculation ID.

        Arguments:
            task_id (str): Calculation ID

        Returns:
            chgcar (dict): Pymatgen CHGCAR object.
        """

        result = self.search(task_ids=task_id, fields=["task_id", "data"], chunk_size=1)

        if len(result) > 0:
            return result[0]["data"]
        else:
            raise MPRestError("No charge density found")

    def get_charge_density_calculation_details(self, task_id: str):
        """
        Get charge density calculations details for a given calculation (task) ID.

        Arguments:
            task_id (str): Calculation (task) ID

        Returns:
            calc_details (dict): Dictionary containing INCAR, POSCAR, and KPOINTS data for the DFT calculation.
        """

        task_rester = TaskRester(endpoint=self.base_endpoint, api_key=self.api_key)  # type: ignore

        result = task_rester.get_document_by_id(
            document_id=task_id,
            fields=["orig_inputs.incar", "orig_inputs.poscar", "orig_inputs.kpoints"],
        ).orig_inputs

        return result

    def get_charge_density_calculation_ids_from_material_id(self, material_id: str):
        """
        Get charge density calculation ids associated with a given Materials Project ID
        that have charge density data.

        Arguments:
            material_id (str): Materials Project ID

        Returns:
            calculation_ids (List[str]): List of calculation ids that have charge density data.
        """

        materials_rester = MaterialsRester(  # type: ignore
            endpoint=self.base_endpoint, api_key=self.api_key,
        )

        mat_doc = materials_rester.get_document_by_id(
            document_id=material_id, fields=["calc_types"]
        )

        calculation_ids = []
        if mat_doc is not None:
            for calculation_id, calculation_type in mat_doc.calc_types.items():
                if "Static" in calculation_type:
                    calculation_ids.append(calculation_id)

        result = []

        if len(calculation_ids) > 0:
            result = self.search(
                task_ids=",".join(calculation_ids),
                fields=["task_id", "last_updated"],
                chunk_size=10,
            )

        return result

    def get_charge_density_from_material_id(self, material_id: str):
        """
        Get charge density data for a given Materials Project ID.

        Arguments:
            material_id (str): Material Project ID

        Returns:
            chgcar (dict): Pymatgen CHGCAR object.
        """

        task_id = sorted(
            self.get_charge_density_calculation_ids_from_material_id(material_id),
            key=lambda d: d["last_updated"],
            reverse=True,
        )[0]["task_id"]

        result = self.search(task_ids=task_id, fields=["task_id", "data"], chunk_size=1)

        if len(result) > 0:
            return result[0]["data"]
        else:
            raise MPRestError("No charge density found")
