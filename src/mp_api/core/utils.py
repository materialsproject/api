import re
from typing import List


def validate_ids(id_list: List[str]):
    """Function to validate material and task IDs

    Args:
        id_list (List[str]): List of material or task IDs.

    Raises:
        ValueError: If at least one ID is not formatted correctly.

    Returns:
        id_list: Returns original ID list if everything is formatted correctly.
    """
    pattern = "(mp|mvc|mol)-.*"

    for entry in id_list:
        if re.match(pattern, entry) is None:
            raise ValueError(f"{entry} is not formatted correctly!")

    return id_list
