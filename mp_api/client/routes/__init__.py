from __future__ import annotations

from mp_api.client.core.utils import LazyImport

GENERIC_RESTERS: dict[str, LazyImport] = {
    k: LazyImport(f"mp_api.client.routes._server.{v}")
    for k, v in {
        "_general_store": "GeneralStoreRester",
        "_messages": "MessagesRester",
        "_user_settings": "UserSettingsRester",
    }.items()
}
