from __future__ import annotations

from emmet.core.mpid_ext import validate_identifier
from monty.json import MSONable

from mp_api.client.core.settings import MAPIClientSettings


def validate_ids(id_list: list[str]):
    """Function to validate material and task IDs.

    Args:
        id_list (List[str]): List of material or task IDs.

    Raises:
        ValueError: If at least one ID is not formatted correctly.

    Returns:
        id_list: Returns original ID list if everything is formatted correctly.
    """
    if len(id_list) > MAPIClientSettings().MAX_LIST_LENGTH:
        raise ValueError(
            "List of material/molecule IDs provided is too long. Consider removing the ID filter to automatically pull"
            " data for all IDs and filter locally."
        )

    # TODO: after the transition to AlphaID in the document models,
    # The following line should be changed to
    # return [validate_identifier(idx,serialize=True) for idx in id_list]
    return [str(validate_identifier(idx)) for idx in id_list]


def allow_msonable_dict(monty_cls: type[MSONable]):
    """Patch Monty to allow for dict values for MSONable."""

    def validate_monty(cls, v, _):
        """Stub validator for MSONable as a dictionary only."""
        if isinstance(v, cls):
            return v
        elif isinstance(v, dict):
            # Just validate the simple Monty Dict Model
            errors = []
            if v.get("@module", "") != monty_cls.__module__:
                errors.append("@module")

            if v.get("@class", "") != monty_cls.__name__:
                errors.append("@class")

            if len(errors) > 0:
                raise ValueError(
                    "Missing Monty seriailzation fields in dictionary: {errors}"
                )

            return v
        else:
            raise ValueError(f"Must provide {cls.__name__} or MSONable dictionary")

    monty_cls.validate_monty_v2 = classmethod(validate_monty)

    return monty_cls
