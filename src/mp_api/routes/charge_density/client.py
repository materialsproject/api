from platform import version
from mp_api.core.client import BaseRester, MPRestError
from mp_api.routes.tasks.client import TaskRester
from mp_api.routes.materials.client import MaterialsRester
from mp_api.routes.charge_density.models import ChgcarDataDoc


class ChargeDensityRester(BaseRester[ChgcarDataDoc]):

    suffix = "charge_density"
    primary_key = "task_id"
    document_model = ChgcarDataDoc

    # TODO: need to move upwards to MPRester to avoid initialization of MaterialsRester ?
    def _get_possible_charge_density_task_ids_from_material_id(self, material_id: str):
        """
        Get charge density calculation ids associated with a given Materials Project ID
        that have charge density data.

        Arguments:
            material_id (str): Materials Project ID

        Returns:
            task_ids (List[str]): List of calculation ids that may have charge density data.
        """

        materials_rester = MaterialsRester(  # type: ignore
            endpoint=self.base_endpoint, api_key=self.api_key,
        )

        mat_doc = materials_rester.get_document_by_id(
            document_id=material_id, fields=["calc_types"]
        )

        task_ids = []
        if mat_doc is not None:
            for task_id, calculation_type in mat_doc.calc_types.items():
                if "Static" in calculation_type:
                    task_ids.append(task_id)

        result = []

        if len(task_ids) > 0:
            result = self.search(
                task_ids=",".join(task_ids),
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
            self._get_possible_charge_density_task_ids_from_material_id(material_id),
            key=lambda d: d["last_updated"],
            reverse=True,
        )[0]["task_id"]

        result = self.search(task_ids=task_id, fields=["task_id", "data"], chunk_size=1)

        if len(result) > 0:
            return result[0]["data"]
        else:
            raise MPRestError("No charge density found")
