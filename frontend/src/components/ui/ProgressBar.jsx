import clsx from "clsx"

const COLOR_MAP = {
  indigo:  "bg-accent-indigo",
  cyan:    "bg-accent-cyan",
  emerald: "bg-accent-emerald",
}

export default function ProgressBar({ value = 0, color = "indigo", animated = false }) {
  return (
    <div className="w-full h-2 bg-bg-tertiary rounded-full overflow-hidden">
      <div
        className={clsx(
          "h-full rounded-full transition-all duration-500",
          COLOR_MAP[color] ?? COLOR_MAP.indigo,
          animated && "relative overflow-hidden"
        )}
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      >
        {animated && (
          <span
            className="absolute inset-0"
            style={{
              background:
                "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.15) 50%, transparent 100%)",
              backgroundSize: "200% 100%",
              animation: "shimmer 2s linear infinite",
            }}
          />
        )}
      </div>
    </div>
  )
}
