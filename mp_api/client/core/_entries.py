"""Progress reporting for client-side entry processing.

Rescaling entries to conventional cells and applying pymatgen corrections or
mixing schemes can take a while for large chemical systems. The helpers here
do that work behind a progress bar (see `_display.progress_bar`), so callers
can see what is being done to their entries rather than a silent block.

pymatgen doesn't report progress from `process_entries`, so `_track_calls`
counts calls to *public* methods it makes once per entry or structure
(`Compatibility.get_adjustments`, `StructureMatcher.group_structures`). If
pymatgen changes how often it calls them, only the bar's accuracy suffers: it's
filled to its total when processing finishes, and the results are unaffected.

The methods are only ever wrapped on private copies (`_private_copy`).
pymatgen's Compatibility classes are monty `@cached_class`es: constructing one
with the same arguments returns the same instance process-wide (and
`copy.copy` returns it too), so wrapping the instance a caller holds would
leak into other threads and later calls.
"""

from __future__ import annotations

from contextlib import ExitStack, contextmanager
from copy import deepcopy
from typing import TYPE_CHECKING

from pymatgen.entries.computed_entries import ComputedStructureEntry
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from mp_api.client.core._display import progress_bar

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from typing import Any

    from pymatgen.entries.compatibility import Compatibility

    from mp_api.client.core._display import ProgressHandle


def _advance(handle: ProgressHandle, amount: float) -> None:
    """Advance `handle` by `amount`, without going past its total."""
    if handle.total is not None:
        amount = min(amount, handle.total - handle.completed)
    if amount > 0:
        handle.update(amount)


@contextmanager
def _track_calls(
    obj: Any,
    name: str,
    handle: ProgressHandle,
    weight: Callable[..., float] | float = 1.0,
) -> Iterator[None]:
    """Advance `handle` each time a call to `obj.<name>` finishes (or raises).

    The method is replaced by an instance attribute for the duration of the
    block and the original lookup is restored afterwards, even on error.

    Args:
        obj : object whose method is counted; should be private to the caller
        name (str) : method name
        handle (ProgressHandle) : bar to advance
        weight (float or callable) : units per call; a callable receives the
            call's arguments, e.g. to count the structures passed in
    """
    original = getattr(obj, name)
    had_own = name in vars(obj)
    own = vars(obj).get(name)

    def counted(*args: Any, **kwargs: Any) -> Any:
        try:
            return original(*args, **kwargs)
        finally:  # also when it raises, e.g. for an entry pymatgen drops
            _advance(handle, weight(*args, **kwargs) if callable(weight) else weight)

    setattr(obj, name, counted)
    try:
        yield
    finally:
        if had_own:
            setattr(obj, name, own)
        else:
            delattr(obj, name)


def _private_copy(obj: Any) -> Any:
    """A shallow copy of `obj` that bypasses monty's `@cached_class` cache.

    Attributes are shared with `obj` (pymatgen only reads them while
    processing); attributes set on the copy, including counted methods and
    state pymatgen records during `process_entries`, stay on the copy.
    """
    clone = object.__new__(type(obj))
    clone.__dict__.update(vars(obj))
    return clone


def get_conventional_cell_entry(
    entry: ComputedStructureEntry,
) -> ComputedStructureEntry:
    """Rebuild `entry` on the standard conventional unit cell, scaling the energy
    and energy adjustments accordingly.
    """
    conventional_structure = SpacegroupAnalyzer(
        entry.structure
    ).get_conventional_standard_structure()
    site_ratio = len(conventional_structure) / len(entry.structure)

    energy_adjustments = deepcopy(entry.energy_adjustments)
    for adjustment in energy_adjustments:  # adjustment values are extensive
        adjustment.normalize(1 / site_ratio)

    return ComputedStructureEntry(
        conventional_structure,
        entry.uncorrected_energy * site_ratio,
        energy_adjustments=energy_adjustments,
        parameters=entry.parameters,
        data=entry.data,
        entry_id=entry.entry_id,
    )


def rescale_to_conventional(
    entries: Sequence[ComputedStructureEntry], *, enabled: bool = True
) -> list[ComputedStructureEntry]:
    """Rebuild each entry on its conventional unit cell, with a progress bar.

    Args:
        entries : entries to rescale
        enabled (bool) : whether to show progress (e.g. `not mute_progress_bars`)
    """
    n = len(entries)
    rescaled = []
    with progress_bar(
        "Rescaling entries to conventional cells",
        total=n,
        enabled=enabled,
        unit="entries",
        summary=f"Rescaled {n:,} {_plural(n)} to conventional unit cells",
        log=f"Rescaling {n:,} {_plural(n)} to conventional unit cells",
    ) as handle:
        for entry in entries:
            rescaled.append(get_conventional_cell_entry(entry))
            handle.update()
    return rescaled


def apply_corrections(
    corrector: Compatibility,
    entries: Sequence[Any],
    *,
    description: str,
    log: str,
    summary: str,
    enabled: bool = True,
) -> list[Any]:
    """Run `corrector.process_entries(entries)` behind a progress bar.

    The bar counts entries. For a mixing scheme, which goes over the entries
    in several passes, each pass is weighted so the bar still ends at the
    number of entries.

    Args:
        corrector (Compatibility) : a correction scheme or mixing scheme. It
            isn't modified: a private copy does the work.
        entries : entries to process
        description (str) : short label next to the bar
        log (str) : logged at INFO when no live bar can be drawn
        summary (str) : completion line; "{kept}" is replaced by the number of
            entries returned, e.g. "Corrected 10 entries ({kept:,} kept)"
        enabled (bool) : whether to show progress
    """
    from pymatgen.entries.compatibility import MaterialsProjectAqueousCompatibility
    from pymatgen.entries.mixing_scheme import MaterialsProjectDFTMixingScheme

    n = len(entries)
    corrector = _private_copy(corrector)
    with (
        progress_bar(
            description, total=n, enabled=enabled, unit="entries", log=log
        ) as handle,
        ExitStack() as stack,
    ):
        if isinstance(corrector, MaterialsProjectDFTMixingScheme):
            # passes: compat_1 corrections (run type 1 entries), structure
            # matching (all entries), then the mixing adjustments (all entries)
            n_1 = sum(
                (getattr(e, "parameters", None) or {}).get("run_type")
                in corrector.valid_rtypes_1
                for e in entries
            )
            unit = n / (2 * n + (n_1 if corrector.compat_1 else 0)) if n else 0.0
            corrector.structure_matcher = _private_copy(corrector.structure_matcher)
            if corrector.compat_1:
                corrector.compat_1 = _private_copy(corrector.compat_1)
                stack.enter_context(
                    _track_calls(corrector.compat_1, "get_adjustments", handle, unit)
                )
            stack.enter_context(
                _track_calls(
                    corrector.structure_matcher,
                    "group_structures",
                    handle,
                    lambda s_list, *a, **k: unit * len(s_list),
                )
            )
            stack.enter_context(
                _track_calls(corrector, "get_adjustments", handle, unit)
            )
        elif (
            isinstance(corrector, MaterialsProjectAqueousCompatibility)
            and corrector.solid_compat
        ):  # solid corrections first, then aqueous ones
            corrector.solid_compat = _private_copy(corrector.solid_compat)
            stack.enter_context(
                _track_calls(corrector.solid_compat, "get_adjustments", handle, 0.5)
            )
            stack.enter_context(
                _track_calls(corrector, "get_adjustments", handle, 0.5)
            )
        else:
            stack.enter_context(_track_calls(corrector, "get_adjustments", handle))

        processed: list[Any] = corrector.process_entries(entries)  # type: ignore[arg-type]
        _advance(handle, n)  # anything pymatgen did without a counted call
        # `progress_bar` formats the summary again, so escape literal braces
        handle.summary = (
            summary.format(kept=len(processed)).replace("{", "{{").replace("}", "}}")
        )
    return processed


def _plural(n: int, word: str = "entry", plural: str = "entries") -> str:
    return word if n == 1 else plural
