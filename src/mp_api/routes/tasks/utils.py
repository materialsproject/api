from pymatgen.core import Structure
from pymatgen.core.trajectory import Trajectory
from collections import defaultdict
from typing import List


def calcs_reversed_to_trajectory(calcs_reversed: List[dict]):
    """
    Converts data from calc_reversed to pymatgen Trajectory objects
    that contain structure, energy, force and stress data for each
    ionic step.

    Args:
        calcs_reversed: List of dictionaries in calcs_reversed entry
            of a task document.
    """
    trajectories = []

    for calculation in calcs_reversed:
        for step in calculation["output"]["ionic_steps"]:

            structures = []
            frame_props = defaultdict(list)  # type: dict

            structures.append(Structure.from_dict(step["structure"]))

            frame_props["e_fr_energy"].append(step["e_fr_energy"])
            frame_props["e_wo_entrp"].append(step["e_wo_entrp"])
            frame_props["e_0_energy"].append(step["e_wo_entrp"])
            frame_props["forces"].append(step["forces"])
            frame_props["stresses"].append(step["stress"])

        traj = Trajectory.from_structures(
            structures, frame_properties=frame_props, time_step=None
        ).as_dict()
        trajectories.append(traj)

    return trajectories
