from maggma.api.resource import ReadOnlyResource
from maggma.api.resource.aggregation import AggregationResource
from mp_api.routes.robocrys.models import RobocrysDoc
from mp_api.routes.robocrys.query_operators import RoboTextSearchQuery


def robo_resource(robo_store):
    resource = ReadOnlyResource(
        robo_store,
        RobocrysDoc,
        tags=["Robocrystallographer"],
        enable_default_search=False,
    )

    return resource


def robo_search_resource(robo_store):
    resource = AggregationResource(
        robo_store,
        RobocrysDoc,
        pipeline_query_operator=RoboTextSearchQuery(),
        tags=["Robocrystallographer"],
        sub_path="/text_search/",
    )

    return resource
