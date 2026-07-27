import { Flag, Footprints, Users, ArrowUpFromLine, MonitorPlay, Zap, Film } from "lucide-react"

// Must mirror backend/constants.py's EventType and HighlightType exactly.

export const EVENT_TYPES = [
  { value: "try", label: "Try", icon: Flag },
  { value: "kick", label: "Kicks", icon: Footprints },
  { value: "card", label: "Card Event", icon: "card" }, // rendered via CardEventIcon
  { value: "scrum", label: "Scrum", icon: Users },
  { value: "lineout", label: "Lineout", icon: ArrowUpFromLine },
  { value: "tmo_replay", label: "TMO/Replay", icon: MonitorPlay },
]

export const EVENT_TYPE_LABELS = Object.fromEntries(
  EVENT_TYPES.map((e) => [e.value, e.label])
)

export const HIGHLIGHT_TYPES = [
  { value: "short", label: "Short", sub: "~3 minutes", icon: Zap },
  { value: "extended", label: "Extended", sub: "10–15 minutes", icon: Film },
]
