import { motion } from "framer-motion"
import clsx from "clsx"

const COLOR_CLASSES = {
  indigo:  "bg-indigo-500/10 text-accent-indigo",
  cyan:    "bg-cyan-500/10 text-accent-cyan",
  emerald: "bg-emerald-500/10 text-accent-emerald",
  amber:   "bg-amber-500/10 text-accent-amber",
  red:     "bg-red-500/10 text-accent-red",
  purple:  "bg-purple-500/10 text-accent-purple",
}

export default function StatCard({ label, value, icon: Icon, trend, color = "indigo" }) {
  const isPositive = trend?.startsWith("+")
  const isNegative = trend?.startsWith("-")

  return (
    <div className="stat-card">
      <div className="flex items-start justify-between">
        <motion.div
          className={clsx("p-3 rounded-xl animate-float", COLOR_CLASSES[color] ?? COLOR_CLASSES.indigo)}
          animate={{ y: [0, -4, 0] }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        >
          {Icon && <Icon size={22} />}
        </motion.div>
        {trend && (
          <span
            className={clsx(
              "text-xs font-semibold px-2 py-0.5 rounded-full",
              isPositive && "bg-emerald-500/10 text-accent-emerald",
              isNegative && "bg-red-500/10 text-accent-red",
              !isPositive && !isNegative && "bg-bg-tertiary text-text-secondary"
            )}
          >
            {trend}
          </span>
        )}
      </div>
      <div>
        <p className="text-2xl font-bold text-text-primary">{value}</p>
        <p className="text-sm text-text-secondary">{label}</p>
      </div>
    </div>
  )
}
