from mp_api.core.resource import ConsumerPostResource, GetResource
from mp_api.routes._consumer.models import UserSettingsDoc
from mp_api.routes._consumer.query_operator import UserSettingsPostQuery, UserSettingsGetQuery


def set_settings_resource(consumer_settings_store):
    resource = ConsumerPostResource(
        consumer_settings_store,
        UserSettingsDoc,
        query_operators=[UserSettingsPostQuery()],
        tags=["Consumer"],
        include_in_schema=False,
    )

    return resource


def get_settings_resource(consumer_settings_store):
    resource = GetResource(
        consumer_settings_store,
        UserSettingsDoc,
        query_operators=[UserSettingsGetQuery()],
        tags=["Consumer"],
        key_fields=["consumer_id", "settings"],
        enable_get_by_key=True,
        enable_default_search=False,
        include_in_schema=False,
    )

    return resource
