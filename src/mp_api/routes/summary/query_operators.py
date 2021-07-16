from sys import version_info
from enum import Enum
from typing import Optional
from fastapi import Query

from maggma.api.query_operator import QueryOperator
from maggma.api.utils import STORE_PARAMS
from emmet.core.summary import SummaryStats

from pymatgen.analysis.magnetism import Ordering

from scipy.stats import gaussian_kde
import numpy as np

from collections import defaultdict

if version_info >= (3, 8):
    from typing import Literal  # type: ignore
else:
    from typing_extensions import Literal


class HasPropsQuery(QueryOperator):
    """
    Method to generate a query on whether a material has a certain property
    """

    def query(
        self,
        has_props: Optional[str] = Query(
            None,
            description="Comma-delimited list of possible properties given by HasPropsEnum to search for.",
        ),
    ) -> STORE_PARAMS:

        crit = {}

        if has_props:
            crit = {
                "has_props": {"$all": [prop.strip() for prop in has_props.split(",")]}
            }

        return {"criteria": crit}


class MaterialIDsSearchQuery(QueryOperator):
    """
    Method to generate a query on search docs using multiple material_id values
    """

    def query(
        self,
        material_ids: Optional[str] = Query(
            None, description="Comma-separated list of material_ids to query on"
        ),
    ) -> STORE_PARAMS:

        crit = {}

        if material_ids:
            crit.update(
                {
                    "material_id": {
                        "$in": [
                            material_id.strip()
                            for material_id in material_ids.split(",")
                        ]
                    }
                }
            )

        return {"criteria": crit}


class SearchIsStableQuery(QueryOperator):
    """
    Method to generate a query on whether a material is stable
    """

    def query(
        self,
        is_stable: Optional[bool] = Query(
            None, description="Whether the material is stable."
        ),
    ):

        crit = {}

        if is_stable is not None:
            crit["is_stable"] = is_stable

        return {"criteria": crit}

    def ensure_indexes(self):  # pragma: no cover
        return [("is_stable", False)]


class SearchHasReconstructedQuery(QueryOperator):
    """
    Method to generate a query on whether a material has any reconstructed surfaces
    """

    def query(
        self,
        has_reconstructed: Optional[bool] = Query(
            None, description="Whether the material has reconstructed surfaces."
        ),
    ):

        crit = {}

        if has_reconstructed is not None:
            crit["has_reconstructed"] = has_reconstructed

        return {"criteria": crit}

    def ensure_indexes(self):  # pragma: no cover
        return [("is_stable", False)]


class SearchMagneticQuery(QueryOperator):
    """
    Method to generate a query for magnetic data in search docs.
    """

    def query(
        self,
        ordering: Optional[Ordering] = Query(
            None, description="Magnetic ordering of the material."
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        if ordering:
            crit["ordering"] = ordering.value

        return {"criteria": crit}

    def ensure_indexes(self):  # pragma: no cover
        return [("ordering", False)]


class SearchIsTheoreticalQuery(QueryOperator):
    """
    Method to generate a query on whether a material is theoretical
    """

    def query(
        self,
        theoretical: Optional[bool] = Query(
            None, description="Whether the material is theoretical."
        ),
    ):

        crit = {}

        if theoretical is not None:
            crit["theoretical"] = theoretical

        return {"criteria": crit}

    def ensure_indexes(self):  # pragma: no cover
        return [("theoretical", False)]


class SearchESQuery(QueryOperator):
    """
    Method to generate a query on search electronic structure data.
    """

    def query(
        self,
        is_gap_direct: Optional[bool] = Query(
            None, description="Whether a band gap is direct or not."
        ),
        is_metal: Optional[bool] = Query(
            None, description="Whether the material is considered a metal."
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        if is_gap_direct is not None:
            crit["is_gap_direct"] = is_gap_direct

        if is_metal is not None:
            crit["is_metal"] = is_metal

        return {"criteria": crit}

    def ensure_indexes(self):  # pragma: no cover

        keys = ["is_gap_direct", "is_metal"]

        return [(key, False) for key in keys]


class SearchStatsQuery(QueryOperator):
    """
    Method to generate a query on search stats data
    """

    def __init__(self, search_doc):
        valid_numeric_fields = tuple(
            sorted(k for k, v in search_doc.__fields__.items() if v.type_ == float)
        )

        def query(
            field: Literal[valid_numeric_fields] = Query(  # type: ignore
                valid_numeric_fields[0],
                title=f"SearchDoc field to query on, must be a numerical field, "
                f"choose from: {', '.join(valid_numeric_fields)}",
            ),
            num_samples: Optional[int] = Query(
                None, title="If specified, will only sample this number of documents.",
            ),
            min_val: Optional[float] = Query(
                None,
                title="If specified, will only consider documents with field values "
                "greater than or equal to this minimum value.",
            ),
            max_val: Optional[float] = Query(
                None,
                title="If specified, will only consider documents with field values "
                "less than or equal to this minimum value.",
            ),
            num_points: int = Query(
                100, title="The number of values in the returned distribution."
            ),
        ) -> STORE_PARAMS:

            self.num_points = num_points
            self.min_val = min_val
            self.max_val = max_val

            if min_val or max_val:
                pipeline = [{"$match": {field: {}}}]  # type: list
                if min_val is not None:
                    pipeline[0]["$match"][field]["$gte"] = min_val
                if max_val is not None:
                    pipeline[0]["$match"][field]["$lte"] = max_val
            else:
                pipeline = []

            if num_samples:
                pipeline.append({"$sample": {"size": num_samples}})

            pipeline.append({"$project": {field: 1, "_id": 0}})

            return {"pipeline": pipeline}

        self.query = query

    def query(self):
        " Stub query function for abstract class "
        pass

    def post_process(self, docs):

        if docs:
            field = list(docs[0].keys())[0]

            num_points = self.num_points
            min_val = self.min_val
            max_val = self.max_val
            num_samples = len(docs)
            warnings = []

            values = [d[field] for d in docs if field in d]
            if min_val is None:
                min_val = min(values)
            if max_val is None:
                max_val = max(values)

            if len(values) != len(docs):
                warnings += [
                    "Some documents have field missing.",
                    f"Only {len(values)} of {len(docs)} ({100*len(values)/len(docs):.2f}%) have {field} field present.",
                ]

            kernel = gaussian_kde(values)

            distribution = list(
                kernel(
                    np.arange(min_val, max_val, step=(max_val - min_val) / num_points,)  # type: ignore
                )
            )

            median = float(np.median(values))
            mean = float(np.mean(values))

            response = SummaryStats(
                field=field,
                num_samples=num_samples,
                min=min_val,
                max=max_val,
                distribution=distribution,
                median=median,
                mean=mean,
                warnings=warnings,
            )

        return [response]


# TODO:
# XAS and GB sub doc query operators
# Add weighted work function to data
# Add dimensionality to search endpoint
# Add "has_reconstructed" data
