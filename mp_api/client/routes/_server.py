"""Define RESTers required by the MP web server."""

from __future__ import annotations

from typing import TYPE_CHECKING

from emmet.core._general_store import GeneralStoreDoc
from emmet.core._messages import MessagesDoc, MessageType
from emmet.core._user_settings import UserSettingsDoc

from mp_api.client.core import BaseRester

if TYPE_CHECKING:
    from datetime import datetime


class GeneralStoreRester(BaseRester):  # pragma: no cover
    suffix = "_general_store"
    document_model = GeneralStoreDoc  # type: ignore
    primary_key = "submission_id"
    use_document_model = False

    def add_item(self, kind: str, markdown: str, meta: dict):  # pragma: no cover
        """Set general store data.

        Args:
            kind: Data type description
            markdown: Markdown data
            meta: Metadata
        Returns:
            Dictionary with written data and submission id.


        Raises:
            MPRestError.
        """
        return self._post_resource(
            body=meta, params={"kind": kind, "markdown": markdown}
        ).get("data")

    def get_items(self, kind):  # pragma: no cover
        """Get general store data.

        Args:
            kind: Data type description
        Returns:
            List of dictionaries with kind, markdown, metadata, and submission_id.


        Raises:
            MPRestError.
        """
        return self.search(kind=kind)


class MessagesRester(BaseRester):  # pragma: no cover
    suffix = "_messages"
    document_model = MessagesDoc  # type: ignore
    primary_key = "title"
    use_document_model = False

    def set_message(
        self,
        title: str,
        body: str,
        type: MessageType = MessageType.generic,
        authors: list[str] | None = None,
    ):  # pragma: no cover
        """Set user settings.

        Args:
            title: Message title
            body: Message text body
            type: Message type
            authors: Message authors
        Returns:
            Dictionary with updated message data


        Raises:
            MPRestError.
        """
        d = {"title": title, "body": body, "type": type.value, "authors": authors or []}

        return self._post_resource(body=d).get("data")

    def get_messages(
        self,
        last_updated: datetime,
        sort_fields: list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ):  # pragma: no cover
        """Get user settings.

        Args:
            last_updated (datetime): Datetime to use to query for newer messages
            sort_fields (List[str]): Fields used to sort results. Prefix with '-' to sort in descending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields to project.

        Returns:
            Dictionary with messages data


        Raises:
            MPRestError.
        """
        query_params = {}

        if sort_fields:
            query_params.update(
                {"_sort_fields": ",".join([s.strip() for s in sort_fields])}
            )

        return self._search(
            last_updated=last_updated,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )


class UserSettingsRester(BaseRester):  # pragma: no cover
    suffix = "_user_settings"
    document_model = UserSettingsDoc  # type: ignore
    primary_key = "consumer_id"
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
        valid_fields = [
            "institution",
            "sector",
            "job_role",
            "is_email_subscribed",
            "agreed_terms",
            "message_last_read",
        ]
        for key in settings:
            if key not in valid_fields:
                raise ValueError(
                    f"Invalid setting key {key}. Must be one of {valid_fields}"
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
        return self._query_resource(
            suburl=f"{consumer_id}", fields=fields, num_chunks=1, chunk_size=1
        ).get("data")
