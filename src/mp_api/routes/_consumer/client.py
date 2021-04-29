from mp_api.routes._consumer.models import UserSettingsDoc
from mp_api.core.client import BaseRester


class UserSettingsRester(BaseRester):

    suffix = "user_settings"
    document_model = UserSettingsDoc  # type: ignore

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
            body=settings, params={"consumer_id": consumer_id}
        ).get("data")

    def get_user_settings(self, consumer_id, settings):
        """
        Get user settings.
        Args:
            consumer_id: Consumer ID for the user
        Returns:
            Dictionary with consumer_id and settings.
        Raises:
            MPRestError
        """
        return self.query(query={"consumer_id": consumer_id}, monty_decode=False)
