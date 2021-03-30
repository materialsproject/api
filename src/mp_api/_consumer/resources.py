from mp_api.core.resource import ConsumerPostResource
from mp_api._consumer.models import UserSettingsDoc
from mp_api._consumer.query_operator import UserSettingsQuery


def set_settings_resource(consumer_settings_store):
    resource = ConsumerPostResource(
        consumer_settings_store,
        UserSettingsDoc,
        query_operators=[UserSettingsQuery()],
        tags=["Consumer"],
    )

    return resource
