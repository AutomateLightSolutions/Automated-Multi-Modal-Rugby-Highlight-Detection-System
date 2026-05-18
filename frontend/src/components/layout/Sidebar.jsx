import { Search, Plus } from "lucide-react"
import { useState } from "react"
import StatusBadge from "../ui/StatusBadge"
import { formatTimeAgo } from "../../utils/formatters"

export default function Sidebar({ matches, selectedId, onSelect, onUploadClick }) {
  const [query, setQuery] = useState("")

  const filtered = matches.filter((m) =>
    m.filename.toLowerCase().includes(query.toLowerCase())
  )

  return (
    <aside className="w-[280px] shrink-0 flex flex-col gap-4 h-[calc(100vh-4rem)] sticky top-16">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-text-primary">Matches</h2>
        {matches.length > 0 && (
          <span className="badge-indigo">{matches.length}</span>
        )}
      </div>

      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
        <input
          className="input pl-9 py-2 text-sm"
          placeholder="Search matches…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {filtered.length === 0 && (
          <p className="text-sm text-text-muted text-center py-8">No matches yet</p>
        )}
        {filtered.map((m) => (
          <button
            key={m.match_id}
            onClick={() => onSelect(m.match_id)}
            className={`w-full text-left p-3 rounded-xl border transition-all duration-200 ${
              selectedId === m.match_id
                ? "border-accent-indigo bg-indigo-500/5 border-l-2"
                : "border-border bg-bg-card hover:border-border-light hover:bg-bg-hover"
            }`}
          >
            <p className="text-sm font-medium text-text-primary truncate">{m.filename}</p>
            <div className="flex items-center gap-2 mt-1.5">
              <StatusBadge status={m.status} />
              <span className="text-xs text-text-muted">{formatTimeAgo(m.uploadedAt)}</span>
            </div>
          </button>
        ))}
      </div>

      <button className="btn-primary w-full flex items-center justify-center gap-2" onClick={onUploadClick}>
        <Plus size={16} />
        Upload New
      </button>
    </aside>
  )
}
