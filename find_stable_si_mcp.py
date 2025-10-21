from __future__ import annotations

from mp_api.mcp.tools import MPMcpTools

tools = MPMcpTools()

stable_si_docs = tools.get_thermo_data(
    formula="Si",
    is_stable=True,
    fields=["material_id", "formula_pretty", "energy_above_hull"],
)

if stable_si_docs:
    print("Found stable silicon structures:")
    for doc in stable_si_docs:
        print(
            f"  Material ID: {doc['material_id']}, "
            f"Formula: {doc['pretty_formula']}, "
            f"Energy Above Hull: {doc['energy_above_hull']}"
        )
else:
    print("No stable silicon structures found.")
