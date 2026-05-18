import { motion } from "framer-motion"

function getGradient(value) {
  if (value < 0.4) return "linear-gradient(90deg, #EF4444, #F59E0B)"
  if (value < 0.7) return "linear-gradient(90deg, #F59E0B, #EAB308)"
  return "linear-gradient(90deg, #10B981, #06B6D4)"
}

export default function ConfidenceBar({ value = 0, showLabel = true }) {
  const pct = Math.round(value * 100)
  return (
    <div className="flex items-center gap-2 w-full">
      <div className="flex-1 h-1.5 bg-bg-tertiary rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          style={{ background: getGradient(value) }}
        />
      </div>
      {showLabel && (
        <span className="text-xs font-mono text-text-secondary w-8 text-right">{pct}%</span>
      )}
    </div>
  )
}
