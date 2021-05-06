from mp_api.core.client import BaseRester, MPRestError
from emmet.core.electronic_structure import ElectronicStructureDoc


class ElectronicStructureRester(BaseRester):

    suffix = "electronic_structure"
    document_model = ElectronicStructureDoc  # type: ignore


class BandStructureRester(BaseRester):

    suffix = "bandstructure"
    document_model = ElectronicStructureDoc  # type: ignore

    def get_bandstructure_from_calculation_id(self, task_id: str):
        """
        Get the band structure pymatgen object associated with a given calculation ID.

        Arguments:
            task_id (str): Calculation ID for the band structure calculation

        Returns:
            bandstructure (dict): BandStructure or BandStructureSymmLine object
        """

        result = self._query_resource(
            criteria={"task_id": task_id}, suburl="object", use_document_model=False
        )

        if result.get("data", None) is not None:
            return result["data"]
        else:
            raise MPRestError("No object found")


class DosRester(BaseRester):

    suffix = "dos"
    document_model = ElectronicStructureDoc  # type: ignore

    def get_dos_from_calculation_id(self, task_id: str):
        """
        Get the density of states pymatgen object associated with a given calculation ID.

        Arguments:
            task_id (str): Calculation ID for the density of states calculation

        Returns:
            bandstructure (dict): CompleteDos object
        """

        result = self._query_resource(
            criteria={"task_id": task_id}, suburl="object", use_document_model=False
        )

        if result.get("data", None) is not None:
            return result["data"]
        else:
            raise MPRestError("No object found")
