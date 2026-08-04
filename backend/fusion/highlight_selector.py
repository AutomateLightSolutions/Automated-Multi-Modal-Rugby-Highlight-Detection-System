"""
Highlight clip selection (pipeline v2) — turns a fusion_run's cells into a
ranked, budget-filled list of highlight clips for one profile ("short" /
"extended").

Pipeline:
  1. Filter cells to the requested events, above MIN_CELL_SCORE.
  2. Group consecutive same-event cells into runs, bridging small gaps.
  3. Fit each run into the profile's [min_clip_sec, max_clip_sec] bounds
     (expand short runs around their peak cell, trim long runs to their
     best-scoring window).
  4. Rank candidates, then greedily fill the profile's duration budget —
     optionally guaranteeing each requested event at least one clip first.
  5. Return clips sorted chronologically, each carrying its confidence rank.
"""
import logging

from constants import BRIDGE_CELLS, FUSION_GRID_SEC, MIN_CELL_SCORE, MIN_GAP_SEC

logger = logging.getLogger(__name__)

NON_BRIDGE_BLOCKING_EVENTS = {"normal_play", "tmo_replay"}


# ---------------------------------------------------------------------------
# Step 2: group cells into event runs, with gap-bridging
# ---------------------------------------------------------------------------

def _matches_request(cell: dict, requested_events: set[str]) -> bool:
    return cell["fused_event"] in requested_events and cell["fused_score"] >= MIN_CELL_SCORE


def _bridgeable(gap_cells: list[dict], gap_start_pos: int, all_cells: list[dict]) -> bool:
    n = len(all_cells)
    for pos in range(gap_start_pos, gap_start_pos + len(gap_cells)):
        cell = all_cells[pos]
        if cell["fused_event"] in NON_BRIDGE_BLOCKING_EVENTS:
            continue
        left = all_cells[pos - 1]["fused_score"] if pos - 1 >= 0 else cell["fused_score"]
        right = all_cells[pos + 1]["fused_score"] if pos + 1 < n else cell["fused_score"]
        neighbour_mean = (left + right) / 2
        if cell["fused_score"] < 0.5 * neighbour_mean:
            return False
    return True


def group_event_runs(all_cells: list[dict], requested_events: set[str]) -> list[dict]:
    """
    Args:
        all_cells: every fusion cell for the match, sorted by cell_index.
        requested_events: the set of event classes the user asked for.

    Returns: list of run dicts:
        {event, cell_indices, global_start_sec, global_end_sec,
         peak_score, mean_score, peak_cell_index}
    """
    n = len(all_cells)

    # Raw runs: maximal consecutive stretches of matching same-event cells.
    raw_runs = []
    i = 0
    while i < n:
        if _matches_request(all_cells[i], requested_events):
            event = all_cells[i]["fused_event"]
            j = i
            while (j + 1 < n and _matches_request(all_cells[j + 1], requested_events)
                   and all_cells[j + 1]["fused_event"] == event):
                j += 1
            raw_runs.append({"event": event, "start_pos": i, "end_pos": j})
            i = j + 1
        else:
            i += 1

    # Merge adjacent same-event raw runs across small bridgeable gaps.
    merged = []
    k = 0
    while k < len(raw_runs):
        current = dict(raw_runs[k])
        while k + 1 < len(raw_runs):
            nxt = raw_runs[k + 1]
            if nxt["event"] != current["event"]:
                break
            gap_start = current["end_pos"] + 1
            gap_end = nxt["start_pos"] - 1
            gap_len = gap_end - gap_start + 1
            if gap_len < 1 or gap_len > BRIDGE_CELLS:
                break
            if not _bridgeable(all_cells[gap_start:gap_end + 1], gap_start, all_cells):
                break
            current["end_pos"] = nxt["end_pos"]
            k += 1
        merged.append(current)
        k += 1

    runs = []
    for run in merged:
        cells = all_cells[run["start_pos"]:run["end_pos"] + 1]
        scores = [c["fused_score"] for c in cells]
        peak_score = max(scores)
        peak_cell = cells[scores.index(peak_score)]
        runs.append({
            "event": run["event"],
            "cell_indices": [c["cell_index"] for c in cells],
            "global_start_sec": cells[0]["global_start_sec"],
            "global_end_sec": cells[-1]["global_end_sec"],
            "peak_score": peak_score,
            "mean_score": sum(scores) / len(scores),
            "peak_cell_index": peak_cell["cell_index"],
        })
    return runs


# ---------------------------------------------------------------------------
# Step 3: fit runs to the profile's clip-length bounds
# ---------------------------------------------------------------------------

def _expand_around_peak(peak_idx: int, min_cells: int, n_cells_total: int) -> tuple[int, int] | None:
    """Symmetric window of exactly min_cells around peak_idx, clamped to
    [0, n_cells_total-1] with overflow pushed to the other side. None if the
    match itself is too short to fit min_cells at all."""
    if min_cells > n_cells_total:
        return None
    left_half = (min_cells - 1) // 2
    right_half = min_cells - 1 - left_half
    start = peak_idx - left_half
    end = peak_idx + right_half
    if start < 0:
        end += -start
        start = 0
    if end > n_cells_total - 1:
        start -= (end - (n_cells_total - 1))
        end = n_cells_total - 1
    start = max(0, start)
    if end - start + 1 < min_cells:
        return None
    return start, end


def _best_window(cells: list[dict], window_cells: int) -> tuple[int, int]:
    """Slide a window_cells-wide window across `cells`, return the
    (start_index, end_index) into `cells` with the highest summed score."""
    best_sum = None
    best_start = 0
    for start in range(0, len(cells) - window_cells + 1):
        window = cells[start:start + window_cells]
        total = sum(c["fused_score"] for c in window)
        if best_sum is None or total > best_sum:
            best_sum = total
            best_start = start
    return best_start, best_start + window_cells - 1


def fit_run_to_profile(run: dict, all_cells_by_index: dict, min_clip_sec: float,
                        max_clip_sec: float, n_cells_total: int) -> list[dict]:
    """
    Returns 1 or 2 candidate clip dicts (rare second candidate — see below)
    fit into [min_clip_sec, max_clip_sec]. Each candidate:
        {event, global_start_sec, global_end_sec, duration_sec, peak_score,
         mean_score, source_cell_start, source_cell_end, cells,
         was_expanded, was_trimmed}
    """
    min_cells = round(min_clip_sec / FUSION_GRID_SEC)
    max_cells = round(max_clip_sec / FUSION_GRID_SEC)
    run_cells = [all_cells_by_index[i] for i in run["cell_indices"]]
    n_run_cells = len(run_cells)

    def _make_candidate(cells: list[dict], was_expanded: bool, was_trimmed: bool) -> dict:
        scores = [c["fused_score"] for c in cells]
        return {
            "event": run["event"],
            "global_start_sec": cells[0]["global_start_sec"],
            "global_end_sec": cells[-1]["global_end_sec"],
            "duration_sec": len(cells) * FUSION_GRID_SEC,
            "peak_score": max(scores),
            "mean_score": sum(scores) / len(scores),
            "source_cell_start": cells[0]["cell_index"],
            "source_cell_end": cells[-1]["cell_index"],
            "cells": [c["cell_index"] for c in cells],
            "was_expanded": was_expanded,
            "was_trimmed": was_trimmed,
        }

    if n_run_cells < min_cells:
        window = _expand_around_peak(run["peak_cell_index"], min_cells, n_cells_total)
        if window is None:
            logger.debug("Run at cell %d dropped: match too short for min_clip_sec=%.1fs",
                         run["peak_cell_index"], min_clip_sec)
            return []
        start, end = window
        cells = [all_cells_by_index[i] for i in range(start, end + 1)]
        return [_make_candidate(cells, was_expanded=True, was_trimmed=False)]

    if n_run_cells > max_cells:
        start_pos, end_pos = _best_window(run_cells, max_cells)
        chosen = run_cells[start_pos:end_pos + 1]
        candidates = [_make_candidate(chosen, was_expanded=False, was_trimmed=True)]

        # Optional second candidate from a sufficiently large, separated remainder.
        if n_run_cells * FUSION_GRID_SEC >= max_clip_sec + 2 * min_clip_sec:
            remainder = run_cells[:start_pos] if start_pos > end_pos - start_pos else run_cells[end_pos + 1:]
            gap_cells_needed = round(MIN_GAP_SEC / FUSION_GRID_SEC)
            if len(remainder) >= min_cells + gap_cells_needed:
                remainder_scores = [c["fused_score"] for c in remainder]
                remainder_peak_pos = remainder_scores.index(max(remainder_scores))
                sub_window = remainder[max(0, remainder_peak_pos - min_cells // 2):][:min_cells]
                if len(sub_window) == min_cells:
                    candidates.append(_make_candidate(sub_window, was_expanded=False, was_trimmed=True))
        return candidates

    return [_make_candidate(run_cells, was_expanded=False, was_trimmed=False)]


# ---------------------------------------------------------------------------
# Steps 4-5: rank, select within budget, event coverage
# ---------------------------------------------------------------------------

def _overlaps_or_too_close(candidate: dict, selected: list[dict], min_gap_sec: float) -> bool:
    return any(
        max(candidate["global_start_sec"] - s["global_end_sec"],
            s["global_start_sec"] - candidate["global_end_sec"]) < min_gap_sec
        for s in selected
    )


def select_highlight_clips(cells: list[dict], profile: dict, requested_events: list[str],
                            match_duration: float, ensure_event_coverage: bool = True) -> list[dict]:
    """
    Full selection pipeline: group -> fit -> rank -> greedy-select -> sort.

    Args:
        cells: every fusion cell for the match (fused_event, fused_score,
            cell_index, global_start_sec, global_end_sec), sorted by cell_index.
        profile: {"budget_sec", "min_clip_sec", "max_clip_sec"} (constants.PROFILES entry).
        requested_events: event classes the user asked for.
        match_duration: total match duration, for boundary clamping.

    Returns: chronologically-sorted clip dicts with a "rank" field (1 = highest confidence).
    """
    if not cells:
        return []

    requested_set = set(requested_events)
    all_cells_by_index = {c["cell_index"]: c for c in cells}
    n_cells_total = len(cells)

    runs = group_event_runs(cells, requested_set)

    candidates = []
    for run in runs:
        candidates.extend(fit_run_to_profile(
            run, all_cells_by_index, profile["min_clip_sec"], profile["max_clip_sec"], n_cells_total,
        ))

    for c in candidates:
        c["_rank_score"] = 0.7 * c["peak_score"] + 0.3 * c["mean_score"]
    ranked = sorted(candidates, key=lambda c: c["_rank_score"], reverse=True)

    selected: list[dict] = []
    selected_ids: set[int] = set()
    running_duration = 0.0
    budget_sec = profile["budget_sec"]
    min_gap_sec = MIN_GAP_SEC

    def _try_select(c: dict) -> bool:
        nonlocal running_duration
        if id(c) in selected_ids:
            return False
        if _overlaps_or_too_close(c, selected, min_gap_sec):
            return False
        if running_duration + c["duration_sec"] > budget_sec:
            return False
        selected.append(c)
        selected_ids.add(id(c))
        running_duration += c["duration_sec"]
        return True

    if ensure_event_coverage:
        for event in requested_events:
            if event == "normal_play":
                continue
            best_for_event = next((c for c in ranked if c["event"] == event), None)
            if best_for_event:
                _try_select(best_for_event)

    for c in ranked:
        _try_select(c)

    for rank, c in enumerate(sorted(selected, key=lambda c: c["_rank_score"], reverse=True), start=1):
        c["rank"] = rank
        del c["_rank_score"]

    selected.sort(key=lambda c: c["global_start_sec"])

    logger.info(
        "Highlight selection: %d candidates -> %d selected (%.1fs / %.1fs budget)",
        len(candidates), len(selected), running_duration, budget_sec,
    )
    return selected
