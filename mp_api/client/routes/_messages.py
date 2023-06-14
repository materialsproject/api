from datetime import datetime
from typing import List

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
        authors: List[str] = None,
    ):  # pragma: no cover
        """
        Set user settings

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

    def get_messages(self, last_updated: datetime):  # pragma: no cover
        """Get user settings.

        Args:
            last_updated: Datetime to use to query for newer messages
        Returns:
            Dictionary with messages data


        Raises:
            MPRestError.
        """
        return self._search(last_updated=last_updated)
