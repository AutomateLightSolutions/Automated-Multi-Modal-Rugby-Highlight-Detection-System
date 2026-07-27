import { motion } from "framer-motion"
import ConfidenceBar from "../ui/ConfidenceBar"
import { formatMatchTime, formatDuration } from "../../utils/formatters"
import { EVENT_TYPE_LABELS } from "../../constants/highlights"

function RankBadge({ rank }) {
  if (rank === 1) return <span title="#1">🥇</span>
  if (rank === 2) return <span title="#2">🥈</span>
  if (rank === 3) return <span title="#3">🥉</span>
  return <span className="text-xs text-text-muted font-mono">#{rank}</span>
}

function EventPill({ type }) {
  if (!type) return <span className="text-text-muted text-xs">—</span>
  return (
    <span className="badge-cyan text-xs">{EVENT_TYPE_LABELS[type] ?? type}</span>
  )
}

export default function SegmentsTable({ segments = [] }) {
  const totalSec = segments.reduce(
    (acc, s) => acc + (s.global_end_sec - s.global_start_sec), 0
  )
  const topConf = segments.length
    ? Math.max(...segments.map((s) => s.fused_confidence ?? 0))
    : 0

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-4 text-sm text-text-secondary">
        <span>
          <span className="text-text-primary font-semibold">{segments.length}</span> highlight segments
        </span>
        <span className="text-border">·</span>
        <span>
          <span className="text-text-primary font-semibold">{formatDuration(totalSec)}</span> total
        </span>
        <span className="text-border">·</span>
        <span>
          Top confidence:{" "}
          <span className="text-accent-emerald font-semibold">{Math.round(topConf * 100)}%</span>
        </span>
      </div>

      <div className="overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-bg-secondary">
              <th className="text-left px-4 py-3 text-text-muted font-medium text-xs uppercase tracking-wider">Rank</th>
              <th className="text-left px-4 py-3 text-text-muted font-medium text-xs uppercase tracking-wider">Time Window</th>
              <th className="text-left px-4 py-3 text-text-muted font-medium text-xs uppercase tracking-wider">Duration</th>
              <th className="text-left px-4 py-3 text-text-muted font-medium text-xs uppercase tracking-wider min-w-[160px]">Confidence</th>
              <th className="text-left px-4 py-3 text-text-muted font-medium text-xs uppercase tracking-wider">Event</th>
            </tr>
          </thead>
          <tbody>
            {segments.map((seg, i) => (
              <motion.tr
                key={seg.segment_id ?? i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className={`border-b border-border last:border-0 group hover:border-l-2 hover:border-accent-indigo transition-all cursor-default
                  ${i % 2 === 0 ? "bg-bg-card" : "bg-bg-tertiary"} hover:bg-indigo-500/5`}
              >
                <td className="px-4 py-3">
                  <RankBadge rank={seg.rank ?? i + 1} />
                </td>
                <td className="px-4 py-3 font-mono text-text-primary text-xs whitespace-nowrap">
                  {formatMatchTime(seg.global_start_sec)} → {formatMatchTime(seg.global_end_sec)}
                </td>
                <td className="px-4 py-3 text-text-secondary text-xs">
                  {formatDuration(seg.global_end_sec - seg.global_start_sec)}
                </td>
                <td className="px-4 py-3 min-w-[160px]">
                  <ConfidenceBar value={seg.fused_confidence ?? 0} showLabel />
                </td>
                <td className="px-4 py-3">
                  <EventPill type={seg.event_type} />
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
