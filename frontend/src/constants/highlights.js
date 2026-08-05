import { Flag, Footprints, Users, ArrowUpFromLine, MonitorPlay, Hand, Layers, PlayCircle, Zap, Film } from "lucide-react"

// Must mirror backend/constants.py's EventClass and HighlightType exactly.
// normal_play is intentionally omitted — it's the "nothing happened" catch-all
// class, not something a user would request a highlight of.

export const EVENT_TYPES = [
  { value: "try", label: "Try", icon: Flag },
  { value: "goal_kick", label: "Goal Kick", icon: Footprints },
  { value: "card_event", label: "Card Event", icon: "card" }, // rendered via CardEventIcon
  { value: "penalty", label: "Penalty", icon: Hand },
  { value: "scrum", label: "Scrum", icon: Users },
  { value: "maul", label: "Maul", icon: Layers },
  { value: "lineout", label: "Lineout", icon: ArrowUpFromLine },
  { value: "kick_off", label: "Kick Off", icon: PlayCircle },
  { value: "tmo_replay", label: "TMO/Replay", icon: MonitorPlay },
]

export const EVENT_TYPE_LABELS = Object.fromEntries(
  EVENT_TYPES.map((e) => [e.value, e.label])
)

// Admin timeline colors — one per EventClass, plus normal_play (muted, it's
// the "nothing happened" catch-all) and null (no data for that module).
export const EVENT_COLORS = {
  try: "#10B981",
  goal_kick: "#06B6D4",
  card_event: "#EF4444",
  penalty: "#F59E0B",
  scrum: "#8B5CF6",
  maul: "#EC4899",
  lineout: "#3B82F6",
  kick_off: "#14B8A6",
  tmo_replay: "#F97316",
  normal_play: "#374151",
}
export const NO_DATA_COLOR = "#1F2937"

export const HIGHLIGHT_TYPES = [
  { value: "short", label: "Short", sub: "~3 minutes", icon: Zap },
  { value: "extended", label: "Extended", sub: "~12 minutes", icon: Film },
]
