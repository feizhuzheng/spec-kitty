"""Shared DRG graph-load helpers for charter resolver and compiler.

Introduced in WP03 of the
``excise-doctrine-curation-and-inline-references-01KP54J6`` mission so that
``src/charter/resolver.py`` and ``src/charter/compiler.py`` no longer
duplicate the built-in+project merge/validate sequence.

Updated in WP03 of ``layered-doctrine-org-layer-01KRNPEE`` to add
``_resolve_org_root()`` and perform three-layer (built-in → org → project)
DRG merging in ``load_validated_graph()``.

Architectural note
------------------
``charter`` sits below ``specify_cli`` in the dependency hierarchy::

    kernel (root) <- doctrine <- charter <- specify_cli

``_resolve_org_root()`` therefore cannot import ``specify_cli`` directly.  The
charter-layer implementation always returns ``None`` (no-config fallback).
Callers in ``specify_cli`` that need config-aware org-root resolution should
resolve the path themselves and pass it explicitly as the *org_root* argument
to :func:`load_validated_graph`.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from doctrine.drg.loader import (
    DRGLoadError,
    has_graph_files,
    load_built_in_graph,
    load_graph_or_dir,
    merge_layers,
)
from doctrine.drg.models import DRGEdge, DRGGraph
from doctrine.drg.validator import assert_valid, duplicate_edge_triples


class OrgDRGFragmentError(Exception):
    """Raised when org-layer DRG content (root graph or drg/ fragment) is
    malformed.

    Deliberately NOT a ``DRGLoadError`` subclass, so it is left uncaught by
    the existing wide ``except DRGLoadError`` in
    ``charter.action_doctrine_bundle._load_action_doctrine_bundle`` and
    propagates to the CLI's generic exception boundary (``charter context``'s
    ``except Exception``), which already reports it as a structurally
    distinguishable failure. Scoped strictly to the org branch (root graph or
    ``drg/`` fragment, loaded by :func:`_load_org_layer`) -- the project-layer
    ``.kittify/doctrine`` load elsewhere in :func:`load_validated_graph` is
    unaffected and continues to raise (and be swallowed as) plain
    ``DRGLoadError``.
    """


def _load_org_root_graph(org_root: Path) -> DRGGraph:
    """Load the root-level org graph, wrapping a malformed load in
    :class:`OrgDRGFragmentError` (IC-03)."""
    try:
        return load_graph_or_dir(org_root)
    except DRGLoadError as exc:
        raise OrgDRGFragmentError(
            f"Malformed org DRG root graph at {org_root}: {exc}"
        ) from exc


def _load_org_drg_fragment(drg_dir: Path) -> DRGGraph:
    """Load the ``drg/`` org fragment, wrapping a malformed load in
    :class:`OrgDRGFragmentError` (IC-03)."""
    try:
        return load_graph_or_dir(drg_dir)
    except DRGLoadError as exc:
        raise OrgDRGFragmentError(
            f"Malformed org DRG drg/ fragment at {drg_dir}: {exc}"
        ) from exc


def _dedup_org_layer_edges(
    graph: DRGGraph,
    *,
    root_edges: Sequence[DRGEdge],
    drg_edges: Sequence[DRGEdge],
) -> DRGGraph:
    """Collapse identically-repeated (source, target, relation) triples to one
    -- but ONLY when the retained and dropped occurrences come from
    DIFFERENT org-layer sources (the root graph vs. the ``drg/`` fragment).

    Scoped strictly to genuinely cross-source duplicates within the
    org-internal root+drg/ sub-merge (FR-003): a triple repeated twice
    within the SAME source (both occurrences in the root graph, or both in
    the ``drg/`` fragment) is a plain authoring bug unrelated to the merge
    and must keep reaching the final ``assert_valid``/``DRGValidationError``
    exactly as it did before this mission -- collapsing it here would
    silently absorb a real defect. A duplicate between the org layer and the
    built-in/project layers is a different scope again and, likewise,
    continues to raise at the final ``assert_valid``.

    *root_edges*/*drg_edges* are the edge lists of the two pre-merge source
    graphs. :func:`~doctrine.drg.loader.merge_layers` combines edges via
    plain list concatenation (no copying), so every edge object in *graph*
    is identity-preserved from one of these two lists -- used here only to
    classify which source a given edge came from, not to redefine what
    counts as a duplicate triple.

    Reuses the canonical :func:`duplicate_edge_triples` definition of
    "duplicate" (C-001) to find every 2nd+ occurrence of a triple; the
    same-source-vs-cross-source classification is a provenance check layered
    on top of that result.

    Filters by object identity (``id(e)``), not value/triple equality:
    ``DRGEdge`` has no custom ``__eq__``, so two identical-triple edges with
    unset ``when``/``reason``/``provenance`` are pydantic-value-equal to each
    other -- a value-equality filter would drop *both* copies, leaving zero
    retained edges instead of the required exactly one.
    """
    root_ids = frozenset(id(edge) for edge in root_edges)
    drg_ids = frozenset(id(edge) for edge in drg_edges)

    def _source_of(edge: DRGEdge) -> str:
        if id(edge) in root_ids:
            return "root"
        if id(edge) in drg_ids:
            return "drg"
        raise AssertionError(  # pragma: no cover -- see docstring: unreachable
            f"edge {edge!r} is not identity-present in either org-layer source"
        )

    retained_source_by_triple: dict[tuple[str, str, str], str] = {}
    for edge in graph.edges:
        triple = (edge.source, edge.target, edge.relation.value)
        retained_source_by_triple.setdefault(triple, _source_of(edge))

    cross_source_duplicate_ids = {
        id(edge)
        for edge in duplicate_edge_triples(graph)
        if _source_of(edge)
        != retained_source_by_triple[(edge.source, edge.target, edge.relation.value)]
    }
    deduped_edges = [
        edge for edge in graph.edges if id(edge) not in cross_source_duplicate_ids
    ]
    return graph.model_copy(update={"edges": deduped_edges})


def _load_org_layer(org_root: Path) -> DRGGraph | None:
    """Load org-pack DRG content from *org_root* and/or *org_root*/drg/.

    Returns ``None`` when neither location has a recognisable graph file
    (the "no org DRG layer" case). Guards the FR-001 P0 zeroing: today's
    unconditional ``load_graph_or_dir(org_root)`` raises ``DRGLoadError``
    on a directory with no root-level graph, even when a guide-compliant
    ``drg/*.graph.yaml`` fragment sits alongside it.

    When both a root-level graph and a ``drg/`` fragment are present, they
    are merged via :func:`merge_layers` (root as ``built_in``, ``drg/`` as
    ``project`` -- ``drg/`` wins on same-URN node-label conflicts) and any
    edge triple duplicated identically across the two sources (one
    occurrence in the root graph, one in the ``drg/`` fragment) is collapsed
    to exactly one retained copy via :func:`_dedup_org_layer_edges` (FR-003,
    IC-02). A triple duplicated within a single source is a same-file
    authoring bug, not a cross-source merge artifact -- it is left alone
    here and still raises ``DRGValidationError`` at the final
    ``assert_valid`` in :func:`load_validated_graph`, exactly as it did
    before this mission.

    Malformed content (invalid YAML or schema-invalid) at either location
    raises :class:`OrgDRGFragmentError` (FR-004, IC-03). The root-level load
    and the ``drg/``-level load are each wrapped *independently* -- via the
    two single-purpose helpers below, never a shared ``try`` block -- so a
    malformed root graph does not take a valid, loadable sibling ``drg/``
    fragment down with it.
    """
    drg_dir = org_root / "drg"
    has_root_graph = has_graph_files(org_root)
    has_drg_layer = has_graph_files(drg_dir)

    if not has_root_graph and not has_drg_layer:
        return None
    if not has_drg_layer:
        return _load_org_root_graph(org_root)
    if not has_root_graph:
        return _load_org_drg_fragment(drg_dir)
    root_graph = _load_org_root_graph(org_root)
    drg_graph = _load_org_drg_fragment(drg_dir)
    merged_org = merge_layers(root_graph, drg_graph)
    return _dedup_org_layer_edges(
        merged_org, root_edges=root_graph.edges, drg_edges=drg_graph.edges
    )


def _resolve_org_root(_repo_root: Path) -> Path | None:
    """Return the configured org doctrine snapshot path, or ``None`` if absent.

    The charter-layer implementation is intentionally inert — it always returns
    ``None``.  The ``repo_root`` parameter is accepted for API compatibility;
    callers in ``specify_cli`` are expected to resolve the org root themselves
    (e.g. via ``specify_cli.doctrine.config``) and supply it explicitly to
    :func:`load_validated_graph`.

    This design keeps the ``charter`` package free of ``specify_cli`` imports,
    satisfying the architectural boundary enforced by
    ``tests/architectural/test_layer_rules.py``.
    """
    return None


def load_validated_graph(repo_root: Path, org_root: Path | None = None) -> DRGGraph:
    """Load the built-in + org + project DRG overlay and validate the result.

    Performs a three-layer merge:

    1. **built-in** — bundled graph bundled with the ``doctrine`` package.
    2. **org** — optional organisation-level snapshot supplied via *org_root*.
       When *org_root* is ``None``, :func:`_resolve_org_root` is called; the
       charter-layer implementation returns ``None`` (no-op).  Callers in
       ``specify_cli`` that need config-aware resolution should resolve the org
       root and pass it explicitly.
    3. **project** — optional per-project overlay at
       ``<repo_root>/.kittify/doctrine``.

    Args:
        repo_root: Project root; used to locate the project overlay at
            ``<repo_root>/.kittify/doctrine``.
        org_root: Explicit org doctrine root.  Pass the path returned by the
            ``specify_cli``-layer org-root resolver when calling from higher
            layers.  Defaults to ``None`` (two-layer built-in+project merge).

    Returns:
        A validated :class:`DRGGraph`.

    Raises:
        ValueError: If :func:`assert_valid` rejects the merged graph
            (dangling edges, duplicate edges, or ``requires`` cycles).
    """
    if org_root is None:
        org_root = _resolve_org_root(repo_root)

    built_in = load_built_in_graph()
    org = _load_org_layer(org_root) if org_root and org_root.exists() else None
    project_dir = repo_root / ".kittify" / "doctrine"
    project = (
        load_graph_or_dir(project_dir)
        if has_graph_files(project_dir)
        else None
    )

    merged = merge_layers(merge_layers(built_in, org), project)
    assert_valid(merged)
    return merged


__all__ = [
    "load_validated_graph",
]
