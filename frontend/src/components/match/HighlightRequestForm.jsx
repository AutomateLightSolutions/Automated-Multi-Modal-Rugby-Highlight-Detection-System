import { useState } from "react"
import { motion } from "framer-motion"
import { Zap, Loader2, Check } from "lucide-react"
import toast from "react-hot-toast"
import { EVENT_TYPES, HIGHLIGHT_TYPES } from "../../constants/highlights"
import { generateHighlight } from "../../lib/api"

function CardEventIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="3" y="5" width="12" height="16" rx="2" transform="rotate(-8 3 5)" fill="#F59E0B" opacity="0.9" />
      <rect x="9" y="4" width="12" height="16" rx="2" transform="rotate(8 9 4)" fill="#EF4444" opacity="0.95" />
    </svg>
  )
}

function HighlightTypeCard({ option, selected, onSelect }) {
  const Icon = option.icon
  return (
    <button
      type="button"
      onClick={() => onSelect(option.value)}
      className={`flex-1 flex items-center gap-3 p-4 rounded-xl border text-left transition-all duration-200
        ${selected
          ? "border-accent-indigo bg-indigo-500/10 shadow-glow-indigo"
          : "border-border bg-bg-tertiary hover:border-border-light hover:bg-bg-hover"}`}
    >
      <div className={`p-2 rounded-lg ${selected ? "bg-accent-indigo text-white" : "bg-bg-hover text-text-secondary"}`}>
        <Icon size={18} />
      </div>
      <div className="min-w-0">
        <p className={`font-semibold text-sm ${selected ? "text-text-primary" : "text-text-secondary"}`}>
          {option.label}
        </p>
        <p className="text-xs text-text-muted">{option.sub}</p>
      </div>
      {selected && <Check size={16} className="ml-auto text-accent-indigo shrink-0" />}
    </button>
  )
}

function EventTypeChip({ option, selected, onToggle }) {
  const isCard = option.icon === "card"
  return (
    <button
      type="button"
      onClick={() => onToggle(option.value)}
      aria-pressed={selected}
      className={`flex items-center gap-2 px-3.5 py-2.5 rounded-xl border text-sm font-medium transition-all duration-200
        ${selected
          ? "border-accent-indigo bg-accent-indigo text-white shadow-glow-indigo"
          : "border-border bg-bg-tertiary text-text-secondary hover:border-border-light hover:bg-bg-hover"}`}
    >
      {isCard ? <CardEventIcon size={16} /> : <option.icon size={16} className={selected ? "text-white" : "text-text-muted"} />}
      {option.label}
    </button>
  )
}

export default function HighlightRequestForm({ matchId, onJobCreated }) {
  const [highlightType, setHighlightType] = useState(null)
  const [selectedEvents, setSelectedEvents] = useState([])
  const [generating, setGenerating] = useState(false)

  const isValid = highlightType !== null && selectedEvents.length > 0

  const toggleEvent = (value) => {
    setSelectedEvents((prev) =>
      prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value]
    )
  }

  const handleGenerate = async () => {
    if (!isValid) return

    setGenerating(true)
    toast("🔄 AI analysis started")
    try {
      const res = await generateHighlight(matchId, highlightType, selectedEvents)
      onJobCreated?.(res.data.job_id)
    } catch (err) {
      toast.error(err?.response?.data?.detail ?? "Failed to start generation")
    } finally {
      setGenerating(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-5"
    >
      <div className="space-y-2.5">
        <p className="text-sm font-medium text-text-secondary">Highlight length</p>
        <div className="flex gap-3">
          {HIGHLIGHT_TYPES.map((option) => (
            <HighlightTypeCard
              key={option.value}
              option={option}
              selected={highlightType === option.value}
              onSelect={setHighlightType}
            />
          ))}
        </div>
      </div>

      <div className="space-y-2.5">
        <p className="text-sm font-medium text-text-secondary">Event types</p>
        <div className="flex flex-wrap gap-2">
          {EVENT_TYPES.map((option) => (
            <EventTypeChip
              key={option.value}
              option={option}
              selected={selectedEvents.includes(option.value)}
              onToggle={toggleEvent}
            />
          ))}
        </div>
      </div>

      {!isValid && (
        <p className="text-xs text-text-muted">
          Select a highlight length and at least one event type.
        </p>
      )}

      <button
        className="btn-primary w-full flex items-center justify-center gap-2"
        onClick={handleGenerate}
        disabled={generating || !isValid}
      >
        {generating ? (
          <><Loader2 size={16} className="animate-spin" /> Generating…</>
        ) : (
          <><Zap size={16} /> Generate Highlight</>
        )}
      </button>
    </motion.div>
  )
}
