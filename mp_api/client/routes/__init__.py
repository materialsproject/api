from __future__ import annotations

from mp_api.client.core.utils import LazyImport

GENERIC_RESTERS = {
    k: LazyImport(f"mp_api.client.routes.{k}.{v}")
    for k, v in {
        "_general_store": "GeneralStoreRester",
        "_messages": "MessagesRester",
        "_user_settings": "UserSettingsRester",
    }.items()
}
