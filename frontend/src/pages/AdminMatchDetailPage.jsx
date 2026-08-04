import { useEffect, useMemo, useRef, useState } from "react"
import { useParams, Link } from "react-router-dom"
import { ArrowLeft } from "lucide-react"
import PageWrapper from "../components/layout/PageWrapper"
import LoadingSpinner from "../components/ui/LoadingSpinner"
import StatusBadge from "../components/ui/StatusBadge"
import AdminTimeline from "../components/match/AdminTimeline"
import { adminGetMatch, adminGetTimeline, adminVideoUrl } from "../lib/api"
import { formatDuration } from "../utils/formatters"

function StatTile({ label, value }) {
  return (
    <div className="glass-card px-4 py-3">
      <p className="text-xs text-text-muted uppercase tracking-wider">{label}</p>
      <p className="text-lg font-semibold text-text-primary mt-0.5">{value}</p>
    </div>
  )
}

export default function AdminMatchDetailPage() {
  const { matchId } = useParams()
  const videoRef = useRef(null)

  const [match, setMatch] = useState(null)
  const [timeline, setTimeline] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    setLoading(true)
    setError(false)
    Promise.all([adminGetMatch(matchId), adminGetTimeline(matchId)])
      .then(([matchRes, timelineRes]) => {
        setMatch(matchRes.data)
        setTimeline(timelineRes.data)
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [matchId])

  const handleSeek = (seconds) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seconds
      videoRef.current.play().catch(() => {})
    }
  }

  const stats = useMemo(() => {
    if (!timeline?.cells?.length) return null
    const cells = timeline.cells
    const disagreements = cells.filter((c) => c.disagreement).length
    const avgScore = cells.reduce((a, c) => a + c.fused_score, 0) / cells.length
    const eventCells = cells.filter((c) => c.fused_event !== "normal_play").length
    return { total: cells.length, disagreements, avgScore, eventCells }
  }, [timeline])

  if (loading) return <PageWrapper><div className="pt-24 max-w-6xl mx-auto px-6"><LoadingSpinner text="Loading…" /></div></PageWrapper>
  if (error || !match) {
    return (
      <PageWrapper>
        <div className="pt-24 max-w-6xl mx-auto px-6 text-accent-red">Failed to load match.</div>
      </PageWrapper>
    )
  }

  return (
    <PageWrapper>
      <div className="pt-16 min-h-screen">
        <div className="max-w-6xl mx-auto px-6 py-8 space-y-6">
          <Link to="/admin" className="inline-flex items-center gap-1.5 text-sm text-text-muted hover:text-text-primary transition-colors">
            <ArrowLeft size={14} /> All matches
          </Link>

          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <h1 className="text-xl font-semibold text-text-primary truncate max-w-2xl">{match.filename}</h1>
              <div className="flex items-center gap-3 mt-2">
                <StatusBadge status={match.status} />
                <span className="badge bg-bg-tertiary text-text-secondary border border-border">
                  {formatDuration(match.duration_sec)}
                </span>
                <span className="badge bg-bg-tertiary text-text-secondary border border-border">
                  pipeline v{match.pipeline_version}
                </span>
              </div>
            </div>
          </div>

          <video
            ref={videoRef}
            controls
            preload="metadata"
            src={adminVideoUrl(matchId)}
            className="w-full rounded-xl border border-border bg-black max-h-[480px]"
          />

          {stats && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <StatTile label="Grid cells" value={stats.total} />
              <StatTile label="Non-normal-play cells" value={stats.eventCells} />
              <StatTile label="Disagreements" value={stats.disagreements} />
              <StatTile label="Avg fused score" value={`${Math.round(stats.avgScore * 100)}%`} />
            </div>
          )}

          <div className="glass-card p-6">
            <p className="text-sm font-semibold text-text-primary mb-4">Prediction timeline</p>
            {!timeline?.cells?.length ? (
              <p className="text-sm text-text-muted">
                No fusion data yet — this match is still processing, or hasn't finished analysis.
              </p>
            ) : (
              <AdminTimeline cells={timeline.cells} duration={match.duration_sec} onSeek={handleSeek} />
            )}
          </div>
        </div>
      </div>
    </PageWrapper>
  )
}
