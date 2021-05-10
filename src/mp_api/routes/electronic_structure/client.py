from mp_api.core.client import BaseRester, MPRestError
from mp_api.routes.electronic_structure.models.core import BSPathType
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
            bandstructure (BandStructure): BandStructure or BandStructureSymmLine object
        """

        result = self._query_resource(
            criteria={"task_id": task_id}, suburl="object", use_document_model=False
        )

        if result.get("data", None) is not None:
            return result["data"]
        else:
            raise MPRestError("No object found")

    def get_bandstructure_from_material_id(
        self, material_id: str, path_type: BSPathType = BSPathType.setyawan_curtarolo,
    ):
        """
        Get the band structure pymatgen object associated with a Materials Project ID.

        Arguments:
            materials_id (str): Materials Project ID for a material
            path_type (BSPathType): k-point path selection convention

        Returns:
            bandstructure (BandStructureSymmLine): BandStructureSymmLine object
        """

        es_rester = ElectronicStructureRester(
            version=self.version, endpoint=self.base_endpoint, api_key=self.api_key
        )

        bs_data = es_rester.get_document_by_id(
            document_id=material_id, fields=["bandstructure"]
        ).bandstructure.dict()

        if bs_data[path_type.value]:
            bs_calc_id = bs_data[path_type.value]["calc_id"]
        else:
            raise MPRestError(
                "No {} band structure data found for {}".format(
                    path_type.value, material_id
                )
            )

        bs_obj = self.get_bandstructure_from_calculation_id(bs_calc_id)

        if bs_obj:
            return bs_obj[0]["data"]
        else:
            raise MPRestError("No band structure object found.")


class DosRester(BaseRester):

    suffix = "dos"
    document_model = ElectronicStructureDoc  # type: ignore

    def get_dos_from_calculation_id(self, task_id: str):
        """
        Get the density of states pymatgen object associated with a given calculation ID.

        Arguments:
            task_id (str): Calculation ID for the density of states calculation

        Returns:
            bandstructure (CompleteDos): CompleteDos object
        """

        result = self._query_resource(
            criteria={"task_id": task_id}, suburl="object", use_document_model=False
        )

        if result.get("data", None) is not None:
            return result["data"]
        else:
            raise MPRestError("No object found")

    def get_dos_from_material_id(self, material_id: str):
        """
        Get the complete density of states pymatgen object associated with a Materials Project ID.

        Arguments:
            materials_id (str): Materials Project ID for a material

        Returns:
            dos (CompleteDos): CompleteDos object
        """

        es_rester = ElectronicStructureRester(
            version=self.version, endpoint=self.base_endpoint, api_key=self.api_key
        )

        dos_data = es_rester.get_document_by_id(
            document_id=material_id, fields=["dos"]
        ).dict()

        if dos_data["dos"]:
            dos_calc_id = dos_data["dos"]["total"]["1"]["calc_id"]
        else:
            raise MPRestError(
                "No density of states data found for {}".format(material_id)
            )

        dos_obj = self.get_dos_from_calculation_id(dos_calc_id)

        if dos_obj:
            return dos_obj[0]["data"]
        else:
            raise MPRestError("No band structure object found.")
