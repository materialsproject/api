from __future__ import annotations

from emmet.core._general_store import GeneralStoreDoc

from mp_api.client.core import BaseRester


class GeneralStoreRester(BaseRester[GeneralStoreDoc]):  # pragma: no cover
    suffix = "_general_store"
    document_model = GeneralStoreDoc  # type: ignore
    primary_key = "submission_id"
    monty_decode = False
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
