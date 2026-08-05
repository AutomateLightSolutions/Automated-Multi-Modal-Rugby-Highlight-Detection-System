/**
 * Merge consecutive fusion cells that share the same event into one block,
 * e.g. cell 0-8s "try" + cell 8-16s "try" -> one 0-16s "try" block. Cells
 * must already be sorted by start time (the admin timeline API returns them
 * ordered by cell_index).
 */
export function mergeAdjacentEvents(cells, getEvent, getScore) {
  if (!cells.length) return []

  const blocks = []
  let current = null

  for (const cell of cells) {
    const event = getEvent(cell) ?? null
    const score = getScore(cell) ?? 0

    if (current && current.event === event && cell.global_start_sec <= current.end + 0.01) {
      current.end = cell.global_end_sec
      current.scores.push(score)
      current.cells.push(cell)
    } else {
      if (current) blocks.push(current)
      current = {
        event,
        start: cell.global_start_sec,
        end: cell.global_end_sec,
        scores: [score],
        cells: [cell],
      }
    }
  }
  if (current) blocks.push(current)

  return blocks.map((b) => ({
    event: b.event,
    start: b.start,
    end: b.end,
    peakScore: Math.max(...b.scores),
    meanScore: b.scores.reduce((a, s) => a + s, 0) / b.scores.length,
    cellCount: b.cells.length,
  }))
}
