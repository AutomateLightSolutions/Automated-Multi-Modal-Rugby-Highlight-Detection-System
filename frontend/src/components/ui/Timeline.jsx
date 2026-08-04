import { useState } from "react"
import { formatMatchTime } from "../../utils/formatters"
import { EVENT_TYPE_LABELS } from "../../constants/highlights"
import FloatingTooltip, { computeTooltipAnchor } from "./FloatingTooltip"

function segmentColor(confidence) {
  if (confidence >= 0.7) return "#10B981"
  if (confidence >= 0.4) return "#06B6D4"
  return "#F59E0B"
}

export default function Timeline({ clips = [], onClick }) {
  const [tooltip, setTooltip] = useState(null)

  if (!clips.length) return null

  const maxEnd = Math.max(...clips.map((c) => c.global_end_sec))
  const totalDuration = maxEnd || 1

  return (
    <div className="space-y-2">
      <div className="relative h-10 bg-bg-tertiary rounded-xl overflow-visible mx-1">
        {clips.map((seg, i) => {
          const left = (seg.global_start_sec / totalDuration) * 100
          const width = ((seg.global_end_sec - seg.global_start_sec) / totalDuration) * 100
          const heightPct = 40 + Math.round((seg.peak_score ?? 0.5) * 60)
          const color = segmentColor(seg.peak_score ?? 0.5)
          return (
            <div
              key={i}
              className="absolute bottom-0 rounded cursor-pointer opacity-80 hover:opacity-100 transition-opacity"
              style={{
                left: `${left}%`,
                width: `${Math.max(width, 0.5)}%`,
                height: `${heightPct}%`,
                backgroundColor: color,
              }}
              onMouseEnter={(e) =>
                setTooltip({ seg, anchor: computeTooltipAnchor(e.currentTarget.getBoundingClientRect()) })
              }
              onMouseLeave={() => setTooltip(null)}
              onClick={() => onClick?.(seg)}
            />
          )
        })}
      </div>

      <div className="flex justify-between text-xs font-mono text-text-muted px-1">
        {[0, 0.25, 0.5, 0.75, 1].map((pct) => (
          <span key={pct}>{formatMatchTime(totalDuration * pct)}</span>
        ))}
      </div>

      <FloatingTooltip anchor={tooltip?.anchor}>
        {tooltip && (
          <>
            <p className="font-mono text-text-primary">
              {formatMatchTime(tooltip.seg.global_start_sec)} →{" "}
              {formatMatchTime(tooltip.seg.global_end_sec)}
            </p>
            <p className="text-text-secondary">
              Peak score: {Math.round((tooltip.seg.peak_score ?? 0) * 100)}%
            </p>
            {tooltip.seg.event && (
              <p className="text-accent-cyan">
                {EVENT_TYPE_LABELS[tooltip.seg.event] ?? tooltip.seg.event}
              </p>
            )}
          </>
        )}
      </FloatingTooltip>
    </div>
  )
}
