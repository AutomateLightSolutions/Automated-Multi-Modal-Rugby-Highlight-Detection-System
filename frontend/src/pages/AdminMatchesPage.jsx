import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { motion } from "framer-motion"
import { Eye } from "lucide-react"
import PageWrapper from "../components/layout/PageWrapper"
import EmptyState from "../components/ui/EmptyState"
import LoadingSpinner from "../components/ui/LoadingSpinner"
import StatusBadge from "../components/ui/StatusBadge"
import { adminListMatches } from "../lib/api"
import { formatDuration, formatTimeAgo } from "../utils/formatters"

function ModuleCounts({ counts }) {
  return (
    <div className="flex gap-3 text-xs font-mono text-text-muted">
      <span>visual: <span className="text-text-secondary">{counts.visual}</span></span>
      <span>audio: <span className="text-text-secondary">{counts.audio}</span></span>
      <span>commentary: <span className="text-text-secondary">{counts.commentary}</span></span>
    </div>
  )
}

export default function AdminMatchesPage() {
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    adminListMatches()
      .then((res) => setMatches(res.data))
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [])

  return (
    <PageWrapper>
      <div className="pt-16 min-h-screen">
        <div className="max-w-6xl mx-auto px-6 py-8 space-y-6">
          <div>
            <h1 className="text-2xl font-semibold text-text-primary">Admin — Matches</h1>
            <p className="text-sm text-text-secondary mt-1">
              Inspect per-module and fused predictions for every processed match.
            </p>
          </div>

          {loading && <div className="glass-card p-6"><LoadingSpinner text="Loading matches…" /></div>}

          {!loading && error && (
            <div className="glass-card p-6 text-accent-red">Failed to load matches.</div>
          )}

          {!loading && !error && matches.length === 0 && (
            <EmptyState title="No matches yet" description="Upload a match to see it here once processed." />
          )}

          {!loading && !error && matches.length > 0 && (
            <div className="overflow-x-auto rounded-xl border border-border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-bg-secondary">
                    <th className="text-left px-4 py-3 text-text-muted font-medium text-xs uppercase tracking-wider">Match</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium text-xs uppercase tracking-wider">Status</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium text-xs uppercase tracking-wider">Duration</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium text-xs uppercase tracking-wider">Module rows</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium text-xs uppercase tracking-wider">Fusion run</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium text-xs uppercase tracking-wider">Uploaded</th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {matches.map((m, i) => (
                    <motion.tr
                      key={m.match_id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.03 }}
                      className={`border-b border-border last:border-0 hover:bg-indigo-500/5 transition-colors
                        ${i % 2 === 0 ? "bg-bg-card" : "bg-bg-tertiary"}`}
                    >
                      <td className="px-4 py-3 max-w-xs">
                        <p className="text-text-primary font-medium truncate" title={m.filename}>{m.filename}</p>
                        <p className="text-xs text-text-muted font-mono">v{m.pipeline_version}</p>
                      </td>
                      <td className="px-4 py-3"><StatusBadge status={m.status} /></td>
                      <td className="px-4 py-3 text-text-secondary">{formatDuration(m.duration_sec)}</td>
                      <td className="px-4 py-3"><ModuleCounts counts={m.module_counts} /></td>
                      <td className="px-4 py-3">
                        {m.active_fusion_run_id ? (
                          <span className="badge-emerald text-xs">active</span>
                        ) : (
                          <span className="text-text-muted text-xs">none yet</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-text-muted text-xs whitespace-nowrap">
                        {formatTimeAgo(m.created_at)}
                      </td>
                      <td className="px-4 py-3">
                        <Link
                          to={`/admin/matches/${m.match_id}`}
                          className="btn-ghost inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5"
                        >
                          <Eye size={13} /> Inspect
                        </Link>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </PageWrapper>
  )
}
