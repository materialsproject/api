from emmet.core._user_settings import UserSettingsDoc
from mp_api.client.core import BaseRester


class UserSettingsRester(BaseRester[UserSettingsDoc]):  # pragma: no cover

    suffix = "_user_settings"
    document_model = UserSettingsDoc  # type: ignore
    primary_key = "consumer_id"
    monty_decode = False
    use_document_model = False

    def set_user_settings(self, consumer_id, settings):  # pragma: no cover
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

    def get_user_settings(self, consumer_id):  # pragma: no cover
        """
        Get user settings.
        Args:
            consumer_id: Consumer ID for the user
        Returns:
            Dictionary with consumer_id and settings.
        Raises:
            MPRestError
        """
        return self.get_data_by_id(consumer_id)
