from mp_api._consumer.models import UserSettingsDoc
from mp_api.core.client import BaseRester


class UserSettingsRester(BaseRester):

    suffix = "user_settings"
    document_model = UserSettingsDoc

    def set_user_settings(self, consumer_id, settings):
        """
        Set user settings.
        Args:
            consumer_id: Consumer ID for the user
            settings: Dictionary with user settings
        Returns:
            Dictionary with consumer_id and write status.
        Raises:
            MPRestError
        """
        return self._post_resource(
            data=settings, params={"consumer_id": consumer_id}
        ).get("data")
