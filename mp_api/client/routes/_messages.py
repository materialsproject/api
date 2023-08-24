from __future__ import annotations

from datetime import datetime

from emmet.core._messages import MessagesDoc, MessageType

from mp_api.client.core import BaseRester


class MessagesRester(BaseRester[MessagesDoc]):  # pragma: no cover
    suffix = "_messages"
    document_model = MessagesDoc  # type: ignore
    primary_key = "title"
    monty_decode = False
    use_document_model = False

    def set_message(
        self,
        title: str,
        body: str,
        type: MessageType = MessageType.generic,
        authors: list[str] = None,
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
