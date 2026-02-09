from __future__ import annotations

from typing import TYPE_CHECKING

from emmet.core.mpid import MPID, AlphaID
from emmet.core.similarity import (
    CrystalNNSimilarity,
    SimilarityDoc,
    SimilarityEntry,
    _vector_to_hex_and_norm,
)
from pymatgen.core import Composition, Structure

from mp_api.client.core import BaseRester, MPRestError
from mp_api.client.core.utils import validate_ids

if TYPE_CHECKING:
    import numpy as np
    from emmet.core.similarity import SimilarityScorer

# This limit seems to be associated with MongoDB vector search
MAX_VECTOR_SEARCH_RESULTS = 10_000


class SimilarityRester(BaseRester):
    suffix = "materials/similarity"
    document_model = SimilarityDoc  # type: ignore
    primary_key = "material_id"

    _fingerprinter: SimilarityScorer | None = None

    def fingerprint_structure(self, structure: Structure) -> np.ndarray:
        """Get the fingerprint of a user-submitted structures."""
        if self._fingerprinter is None:
            self._fingerprinter = CrystalNNSimilarity()
        return self._fingerprinter._featurize_structure(structure)

    def search(
        self,
        material_ids: str | list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[SimilarityDoc] | list[dict]:
        """Query similarity docs using a variety of search criteria.

        Arguments:
            material_ids (str, List[str]): A single Material ID string or list of strings
                (e.g., mp-149, [mp-149, mp-13]).
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in SimilarityDoc to return data for.
                Default is material_id, last_updated, and formula_pretty if all_fields is False.

        Returns:
            ([SimilarityDoc], [dict]) List of similarity documents or dictionaries.
        """
        query_params: dict = {}

        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

        query_params = {
            entry: query_params[entry]
            for entry in query_params
            if query_params[entry] is not None
        }
        return super()._search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )

    def find_similar(
        self,
        structure_or_mpid: Structure | str | MPID | AlphaID,
        top: int | None = 50,
        num_chunks: int | None = None,
        chunk_size: int | None = 1000,
    ) -> list[SimilarityEntry] | list[dict]:
        """Find structures most similar to a user-submitted structure.

        Arguments:
            structure_or_mpid : pymatgen .Structure, or str, MPID, AlphaID
                If a .Structure, the feature vector is computed on the fly
                If a str, MPID, or AlphaID, attempts to retrieve a pre-computed
                feature vector using the input as a material ID
            top : int
                The number of most similar materials to return, defaults to 50.
                Setting to None will return the maximum possible number of
                most similar materials..
            num_chunks (int or None): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int or None): Number of data entries per chunk.
                The chunk_size is also used to limit the number of responses returned.

        Returns:
            ([SimilarityEntry] | [dict]) List of SimilarityEntry documents
            (if `use_document_model`) or dict (otherwise) listing
            structures most similar to the input structure.
        """
        if isinstance(structure_or_mpid, str | MPID | AlphaID):
            fmt_idx = AlphaID(structure_or_mpid).string

            docs = self.search(material_ids=[fmt_idx], fields=["feature_vector"])
            if not docs:
                raise MPRestError(f"No similarity data available for {fmt_idx}")
            feature_vector = docs[0]["feature_vector"]

        elif isinstance(structure_or_mpid, Structure):
            feature_vector = self.fingerprint_structure(structure_or_mpid)

        else:
            raise MPRestError(
                "Please submit a pymatgen Structure or MP ID, found ."
                f"structure_or_mpid = {type(structure_or_mpid)}."
            )

        top = top or MAX_VECTOR_SEARCH_RESULTS
        if not isinstance(top, int) or top < 1:
            raise ValueError(
                f"Invalid number of possible top matches specified = {top}."
                "Please specify a positive integer or `None` to return all results."
            )

        vector_hex, vector_norm = _vector_to_hex_and_norm(feature_vector)
        result = self._query_resource(
            criteria={
                "feature_vector_hex": vector_hex,
                "feature_vector_norm": vector_norm,
                "_limit": top,
            },
            suburl="match",
            use_document_model=False,  # Return type is not exactly a SimilarityDoc, closer to SimilarityEntry
            chunk_size=chunk_size,
            num_chunks=num_chunks,
        ).get("data", None)

        if result is None:
            raise MPRestError(
                "Could not find any structures similar to the input structure."
            )

        sim_docs = [
            {
                "formula": entry["formula_pretty"],
                "task_id": entry["material_id"],
                "nelements": len(Composition(entry["formula_pretty"]).elements),
                "dissimilarity": 100 * (1.0 - entry["score"]),
            }
            for entry in result
        ]

        if self.use_document_model:
            return [SimilarityEntry(**doc) for doc in sim_docs]
        return sim_docs
