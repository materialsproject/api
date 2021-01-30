from typing import Optional, Tuple, List

import numpy as np
from fastapi import Query
from scipy.stats import gaussian_kde

from mp_api.core.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.core.resource import Resource
from mp_api.materials.query_operators import (
    FormulaQuery,
    MinMaxQuery,
    SymmetryQuery,
    DeprecationQuery,
)
from mp_api.search.models import SearchDoc, SearchStats
from mp_api.search.query_operators import (
    SearchBandGapQuery,
    HasPropsQuery,
    ThermoEnergySearchQuery,
    SearchTaskIDsQuery,
    SearchIsStableQuery,
    SearchElasticityQuery,
    SearchMagneticQuery,
    SearchDielectricPiezoQuery,
)
from mp_api.surface_properties.query_operators import SurfaceMinMaxQuery


def search_resource(search_store):
    def generate_stats_prep(self):
        model_name = self.model.__name__

        async def generate_stats(
            field: str = Query(
                None,
                title=f"SearchDoc field to query on, must be a numerical field, "
                      f"choose from: {', '.join(SearchDoc().__fields__.keys())}",
            ),
            sample: Optional[int] = Query(
                None, title="If specified, will only sample this number of documents.",
            ),
            # TODO: is there a better type hint than List[float]? e.g. Tuple[float, float]
            min_max: Optional[List[float]] = Query(
                None,
                title="If specified, will only consider documents with field values "
                "within this range (inclusive).",
            ),
        ):
            """
            Generate statistics for a given numerical field specified in SearchDoc.

            Returns:
                A SearchStats object.
            """

            self.store.connect()

            if min_max:
                pipeline = [{"$match": {field: {"$gte": min_max[0], "$lte": min_max[1]}}}]
            else:
                pipeline = []

            if sample:
                pipeline.append({"$sample": {"size": sample}})

            pipeline.append({"$project": {field: 1}})

            values = [
                d[field]
                for d in self.store._collection.aggregate(pipeline, allowDiskUse=True)
            ]
            kernel = gaussian_kde(values)

            if not min_max:
                min_max = [min(values), max(values)]

            num_points = 100
            distribution = list(
                kernel(
                    np.arange(
                        min_max[0],
                        min_max[1],
                        step=(min_max[1] - min_max[0]) / num_points,
                    )
                )
            )

            response = dict(
                field=field, sample=sample, min_max=min_max, distribution=distribution,
            )

            return response

        self.router.get(
            "/generate_statistics/",
            response_model=SearchStats,
            response_model_exclude_unset=True,
            response_description=f"Generate statistics for a given field as {model_name}",
            tags=self.tags,
        )(generate_stats)

    resource = Resource(
        search_store,
        SearchDoc,
        query_operators=[
            SearchTaskIDsQuery(),
            FormulaQuery(),
            MinMaxQuery(),
            SymmetryQuery(),
            ThermoEnergySearchQuery(),
            SearchIsStableQuery(),
            SearchBandGapQuery(),
            SearchElasticityQuery(),
            SearchDielectricPiezoQuery(),
            SurfaceMinMaxQuery(),
            SearchMagneticQuery(),
            HasPropsQuery(),
            DeprecationQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(SearchDoc, default_fields=["task_id"]),
        ],
        custom_endpoint_funcs=[generate_stats_prep],
        tags=["Search"],
    )

    return resource
