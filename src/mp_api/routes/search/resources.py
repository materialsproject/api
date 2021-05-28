from typing import Optional
from typing_extensions import Literal

import numpy as np
from fastapi import Query
from scipy.stats import gaussian_kde

from maggma.api.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from maggma.api.resource import ReadOnlyResource
from mp_api.routes.materials.query_operators import (
    ElementsQuery,
    FormulaQuery,
    MinMaxQuery,
    SymmetryQuery,
    DeprecationQuery,
)
from mp_api.routes.search.models import SearchDoc, SearchStats
from mp_api.routes.search.query_operators import (
    MaterialIDsSearchQuery,
    HasPropsQuery,
    SearchIsStableQuery,
    SearchElasticityQuery,
    SearchMagneticQuery,
    SearchDielectricPiezoQuery,
    SearchIsTheoreticalQuery,
)

# from mp_api.routes.surface_properties.query_operators import SurfaceMinMaxQuery
from mp_api.routes.electronic_structure.query_operators import ESSummaryDataQuery
from mp_api.routes.thermo.query_operators import ThermoEnergyQuery


def search_resource(search_store):
    def generate_stats_prep(self):
        model_name = self.model.__name__

        # we can only generate statistics for fields that return numbers
        valid_numeric_fields = tuple(
            sorted(k for k, v in SearchDoc().__fields__.items() if v.type_ == float)
        )

        async def generate_stats(
            field: Literal[valid_numeric_fields] = Query(
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
        ):
            """
            Generate statistics for a given numerical field specified in SearchDoc.

            Returns:
                A SearchStats object.
            """

            self.store.connect()

            if min_val or max_val:
                pipeline = [{"$match": {field: {}}}]  # type: list
                if min_val:
                    pipeline[0]["$match"][field]["$gte"] = min_val
                if max_val:
                    pipeline[0]["$match"][field]["$lte"] = max_val
            else:
                pipeline = []

            if num_samples:
                pipeline.append({"$sample": {"size": num_samples}})

            pipeline.append({"$project": {field: 1}})

            values = [
                d[field]
                for d in self.store._collection.aggregate(pipeline, allowDiskUse=True)
            ]
            if not min_val:
                min_val = min(values)
            if not max_val:
                max_val = max(values)

            kernel = gaussian_kde(values)

            distribution = list(
                kernel(
                    np.arange(min_val, max_val, step=(max_val - min_val) / num_points,)  # type: ignore
                )
            )

            median = float(np.median(values))
            mean = float(np.mean(values))

            response = SearchStats(
                field=field,
                num_samples=num_samples,
                min=min_val,
                max=max_val,
                distribution=distribution,
                median=median,
                mean=mean,
            )

            return response

        self.router.get(
            "/generate_statistics/",
            response_model=SearchStats,
            response_model_exclude_unset=True,
            response_description=f"Generate statistics for a given field as {model_name}",
            tags=self.tags,
        )(generate_stats)

    resource = ReadOnlyResource(
        search_store,
        SearchDoc,
        query_operators=[
            MaterialIDsSearchQuery(),
            FormulaQuery(),
            ElementsQuery(),
            MinMaxQuery(),
            SymmetryQuery(),
            ThermoEnergyQuery(),
            SearchIsStableQuery(),
            SearchIsTheoreticalQuery(),
            ESSummaryDataQuery(),
            SearchElasticityQuery(),
            SearchDielectricPiezoQuery(),
            # SurfaceMinMaxQuery(),
            SearchMagneticQuery(),
            HasPropsQuery(),
            DeprecationQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(SearchDoc, default_fields=["material_id"]),
        ],
        custom_endpoint_funcs=[generate_stats_prep],
        tags=["Search"],
    )

    return resource
