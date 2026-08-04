import { useState } from "react"
import { AlertTriangle, MousePointerClick } from "lucide-react"
import { EVENT_COLORS, EVENT_TYPE_LABELS, NO_DATA_COLOR } from "../../constants/highlights"
import { formatMatchTime } from "../../utils/formatters"
import { mergeAdjacentEvents } from "../../utils/timelineMerge"
import FloatingTooltip, { computeTooltipAnchor } from "../ui/FloatingTooltip"

function eventLabel(event) {
  if (!event) return "No data"
  return EVENT_TYPE_LABELS[event] ?? event
}

function audioScoreColor(score) {
  // Low -> muted, high -> bright cyan, matching the module-lane accent color.
  const s = Math.max(0, Math.min(1, score ?? 0))
  const lightness = 20 + s * 35
  return `hsl(190, 80%, ${lightness}%)`
}

function TimelineTooltipContent({ tooltip }) {
  const { block, laneKey } = tooltip
  return (
    <>
      <p className="font-mono text-text-primary">
        {formatMatchTime(block.start)} → {formatMatchTime(block.end)}
      </p>
      {laneKey === "audio" ? (
        <p className="text-text-secondary">Score: {Math.round((block.peakScore ?? 0) * 100)}%</p>
      ) : laneKey === "disagreement" ? (
        <p className="text-accent-red flex items-center gap-1"><AlertTriangle size={12} /> Modules disagreed here</p>
      ) : (
        <>
          <p className="text-accent-cyan">{eventLabel(block.event)}</p>
          <p className="text-text-secondary">
            Peak {Math.round(block.peakScore * 100)}% · Mean {Math.round(block.meanScore * 100)}%
          </p>
          <p className="text-text-muted">{block.cellCount} cell{block.cellCount > 1 ? "s" : ""} merged</p>
        </>
      )}
    </>
  )
}

function Lane({ label, blocks, totalDuration, onBlockClick, onHover, colorFor, laneKey }) {
  const handleEnter = (e, block) => {
    const rect = e.currentTarget.getBoundingClientRect()
    onHover({ block, laneKey, anchor: computeTooltipAnchor(rect) })
  }

  const handleClick = (e, block) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const fraction = rect.width > 0 ? (e.clientX - rect.left) / rect.width : 0
    const time = block.start + fraction * (block.end - block.start)
    onBlockClick(time)
  }

  return (
    <div className="flex items-center gap-3">
      <span className="w-24 shrink-0 text-xs font-medium text-text-muted uppercase tracking-wider">{label}</span>
      <div className="relative h-6 flex-1 rounded-md overflow-hidden bg-bg-tertiary">
        {blocks.map((block, i) => {
          const left = (block.start / totalDuration) * 100
          const width = Math.max(((block.end - block.start) / totalDuration) * 100, 0.15)
          return (
            <div
              key={`${laneKey}-${i}`}
              className="absolute top-0 bottom-0 cursor-pointer opacity-90 hover:opacity-100 hover:z-10 hover:outline hover:outline-1 hover:outline-white/40 transition-opacity"
              style={{ left: `${left}%`, width: `${width}%`, backgroundColor: colorFor(block) }}
              onClick={(e) => handleClick(e, block)}
              onMouseEnter={(e) => handleEnter(e, block)}
              onMouseLeave={() => onHover(null)}
            />
          )
        })}
      </div>
    </div>
  )
}

function ModuleDetail({ label, event, score, confidence, highlight = false }) {
  return (
    <div className={`rounded-lg p-3 border ${highlight ? "border-accent-indigo bg-indigo-500/10" : "border-border bg-bg-tertiary"}`}>
      <p className="text-[10px] uppercase tracking-wider text-text-muted font-semibold mb-1.5">{label}</p>
      {event !== undefined && (
        <p className="text-sm font-medium text-text-primary">{eventLabel(event)}</p>
      )}
      {score != null && (
        <p className="text-xs text-text-secondary mt-0.5">
          Score {Math.round(score * 100)}%
          {confidence != null && ` · Confidence ${Math.round(confidence * 100)}%`}
        </p>
      )}
    </div>
  )
}

export default function AdminTimeline({ cells = [], duration, onSeek }) {
  const [tooltip, setTooltip] = useState(null)
  const [selectedCell, setSelectedCell] = useState(null)

  if (!cells.length || !duration) return null

  const visualBlocks = mergeAdjacentEvents(
    cells, (c) => c.contributions?.visual?.event, (c) => c.contributions?.visual?.highlight_score,
  )
  const commentaryBlocks = mergeAdjacentEvents(
    cells, (c) => c.contributions?.commentary?.event, (c) => c.contributions?.commentary?.highlight_score,
  )
  const fusedBlocks = mergeAdjacentEvents(cells, (c) => c.fused_event, (c) => c.fused_score)

  const audioBlocks = cells.map((c) => ({
    event: null,
    start: c.global_start_sec,
    end: c.global_end_sec,
    peakScore: c.contributions?.audio?.highlight_score ?? 0,
    meanScore: c.contributions?.audio?.highlight_score ?? 0,
    cellCount: 1,
  }))

  const disagreementBlocks = mergeAdjacentEvents(
    cells,
    (c) => (c.disagreement ? "disagreement" : "agree"),
    () => 1,
  ).filter((b) => b.event === "disagreement")

  const eventColor = (block) => EVENT_COLORS[block.event] ?? NO_DATA_COLOR

  const handleBlockClick = (time) => {
    onSeek(time)
    const cell = cells.find((c) => time >= c.global_start_sec && time < c.global_end_sec) ?? cells[cells.length - 1]
    setSelectedCell(cell)
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Lane laneKey="fused" label="Fused" blocks={fusedBlocks} totalDuration={duration} onBlockClick={handleBlockClick} onHover={setTooltip} colorFor={eventColor} />
        <Lane laneKey="visual" label="Visual" blocks={visualBlocks} totalDuration={duration} onBlockClick={handleBlockClick} onHover={setTooltip} colorFor={eventColor} />
        <Lane laneKey="commentary" label="Commentary" blocks={commentaryBlocks} totalDuration={duration} onBlockClick={handleBlockClick} onHover={setTooltip} colorFor={eventColor} />
        <Lane laneKey="audio" label="Audio" blocks={audioBlocks} totalDuration={duration} onBlockClick={handleBlockClick} onHover={setTooltip} colorFor={(b) => audioScoreColor(b.peakScore)} />
        {disagreementBlocks.length > 0 && (
          <Lane laneKey="disagreement" label="Disagreement" blocks={disagreementBlocks} totalDuration={duration} onBlockClick={handleBlockClick} onHover={setTooltip} colorFor={() => "#EF4444"} />
        )}
      </div>

      <div className="flex justify-between text-xs font-mono text-text-muted px-1 pl-[6.75rem]">
        {[0, 0.25, 0.5, 0.75, 1].map((pct) => (
          <span key={pct}>{formatMatchTime(duration * pct)}</span>
        ))}
      </div>

      <div className="flex flex-wrap gap-x-4 gap-y-1 pl-[6.75rem]">
        {Object.entries(EVENT_COLORS).map(([event, color]) => (
          <span key={event} className="flex items-center gap-1.5 text-[11px] text-text-muted">
            <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: color }} />
            {eventLabel(event)}
          </span>
        ))}
      </div>

      <FloatingTooltip anchor={tooltip?.anchor}>
        {tooltip && <TimelineTooltipContent tooltip={tooltip} />}
      </FloatingTooltip>

      <div className="rounded-xl border border-border bg-bg-tertiary p-4 min-h-[112px]">
        {!selectedCell ? (
          <div className="flex items-center gap-2 text-xs text-text-muted h-full">
            <MousePointerClick size={14} />
            Click anywhere on the timeline to inspect every module's prediction at that moment.
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="font-mono text-sm text-text-primary">
                {formatMatchTime(selectedCell.global_start_sec)} → {formatMatchTime(selectedCell.global_end_sec)}
              </p>
              {selectedCell.disagreement && (
                <span className="flex items-center gap-1 text-xs text-accent-red">
                  <AlertTriangle size={12} /> Disagreement
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <ModuleDetail
                label="Visual"
                event={selectedCell.contributions?.visual?.event}
                score={selectedCell.contributions?.visual?.highlight_score}
                confidence={selectedCell.contributions?.visual?.event_confidence}
              />
              <ModuleDetail
                label="Commentary"
                event={selectedCell.contributions?.commentary?.event}
                score={selectedCell.contributions?.commentary?.highlight_score}
                confidence={selectedCell.contributions?.commentary?.event_confidence}
              />
              <ModuleDetail
                label="Audio"
                score={selectedCell.contributions?.audio?.highlight_score}
              />
              <ModuleDetail
                label="Fused"
                event={selectedCell.fused_event}
                score={selectedCell.fused_score}
                confidence={selectedCell.fused_event_confidence}
                highlight
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
