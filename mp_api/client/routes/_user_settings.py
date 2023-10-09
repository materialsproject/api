from __future__ import annotations

from emmet.core._user_settings import UserSettingsDoc

from mp_api.client.core import BaseRester


class UserSettingsRester(BaseRester[UserSettingsDoc]):  # pragma: no cover
    suffix = "_user_settings"
    document_model = UserSettingsDoc  # type: ignore
    primary_key = "consumer_id"
    monty_decode = False
    use_document_model = False

    def create_user_settings(self, consumer_id, settings):
        """Create user settings.

        Args:
            consumer_id: Consumer ID for the user
            settings: Dictionary with user settings that
             use UserSettingsDoc schema
        Returns:
            Dictionary with consumer_id and write status.
        """
        return self._post_resource(
            body=settings, params={"consumer_id": consumer_id}
        ).get("data")

    def patch_user_settings(self, consumer_id, settings):  # pragma: no cover
        """Patch user settings.

        Args:
            consumer_id: Consumer ID for the user
            settings: Dictionary with user settings
        Returns:
            Dictionary with consumer_id and write status.


        Raises:
            MPRestError.
        """
        body = dict()
        for key in settings:
            if key not in [
                "institution",
                "sector",
                "job_role",
                "is_email_subscribed",
                "agreed_terms",
            ]:
                raise ValueError(
                    f"Invalid setting key {key}. Must be one of"
                    "institution, sector, job_role, is_email_subscribed, agreed_terms"
                )
            body[f"settings.{key}"] = settings[key]

        return self._patch_resource(body=body, params={"consumer_id": consumer_id}).get(
            "data"
        )

    def patch_user_time_settings(self, consumer_id, time):  # pragma: no cover
        """Set user settings last_read_message field.

        Args:
            consumer_id: Consumer ID for the user
            time: utc datetime object for when the user last see messages
        Returns:
            Dictionary with consumer_id and write status.


        Raises:
            MPRestError.
        """
        return self._patch_resource(
            body={"settings.message_last_read": time.isoformat()},
            params={"consumer_id": consumer_id},
        ).get("data")

    def get_user_settings(self, consumer_id, fields):  # pragma: no cover
        """Get user settings.

        Args:
            consumer_id: Consumer ID for the user
            fields: List of fields to project
        Returns:
            Dictionary with consumer_id and settings.


        Raises:
            MPRestError.
        """
        return self.get_data_by_id(consumer_id, fields)
