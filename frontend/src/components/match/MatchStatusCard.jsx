import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { CheckCircle, Loader2, AlertCircle, XCircle } from "lucide-react"
import { useMatchPolling } from "../../hooks/useMatchPolling"
import { getMatchHighlights } from "../../lib/api"
import StatusBadge from "../ui/StatusBadge"
import LoadingSpinner from "../ui/LoadingSpinner"
import HighlightRequestForm from "./HighlightRequestForm"
import HighlightJobsList from "./HighlightJobsList"
import { formatDuration } from "../../utils/formatters"

const STAGES = [
  { key: "uploaded",    label: "Uploaded" },
  { key: "extracting", label: "Extracting" },
  { key: "processing", label: "Processing" },
  { key: "done",       label: "Complete" },
]

const STAGE_ORDER = { uploaded: 0, extracting: 1, processing: 2, done: 3 }

function PipelineStepper({ status }) {
  const isFailed = status === "failed"
  const current = STAGE_ORDER[status] ?? 0

  return (
    <div className="flex items-center gap-2">
      {STAGES.map((stage, i) => {
        const done = i < current
        const active = i === current && !isFailed
        const future = i > current
        return (
          <div key={stage.key} className="flex items-center">
            <div className="flex flex-col items-center gap-1">
              <div className={`relative w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300
                ${isFailed
                  ? "bg-red-500/20 border border-red-500/40"
                  : done
                    ? "bg-accent-emerald"
                    : active
                      ? "bg-accent-indigo"
                      : "bg-bg-tertiary border border-border"}`}
              >
                {isFailed ? (
                  <XCircle size={14} className="text-red-400" />
                ) : done ? (
                  <CheckCircle size={14} className="text-white" />
                ) : active ? (
                  <>
                    <Loader2 size={14} className="text-white animate-spin" />
                    <span className="absolute inset-0 rounded-full border-2 border-accent-indigo animate-ping opacity-50" />
                  </>
                ) : (
                  <span className={`text-xs font-bold ${future ? "text-text-muted" : "text-white"}`}>{i + 1}</span>
                )}
              </div>
              <span className={`text-[10px] font-medium whitespace-nowrap ${
                isFailed ? "text-red-400" : active ? "text-accent-indigo" : done ? "text-accent-emerald" : "text-text-muted"
              }`}>
                {stage.label}
              </span>
            </div>
            {i < STAGES.length - 1 && (
              <div className={`w-8 h-0.5 mb-4 mx-1 transition-colors duration-300 ${
                isFailed ? "bg-red-500/20" : i < current ? "bg-accent-emerald" : "bg-border"
              }`} />
            )}
          </div>
        )
      })}
    </div>
  )
}

export default function MatchStatusCard({ matchId, onStatusChange }) {
  const { data, isLoading, isError } = useMatchPolling(matchId)
  const [jobs, setJobs] = useState([])

  useEffect(() => {
    if (data?.status) onStatusChange?.(data.status)
  }, [data?.status, onStatusChange])

  useEffect(() => {
    setJobs([])
    getMatchHighlights(matchId)
      .then((res) => setJobs(res.data.map((j) => ({ job_id: j.job_id }))))
      .catch(() => setJobs([]))
  }, [matchId])

  const handleJobCreated = (jobId) => {
    setJobs((prev) => [{ job_id: jobId }, ...prev])
  }

  const handleJobDeleted = (jobId) => {
    setJobs((prev) => prev.filter((j) => j.job_id !== jobId))
  }

  if (isLoading) return <div className="glass-card p-6"><LoadingSpinner text="Loading match status…" /></div>
  if (isError || !data) return (
    <div className="glass-card p-6 flex items-center gap-3 text-accent-red">
      <AlertCircle size={20} />
      <p>Failed to load match status.</p>
    </div>
  )

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-6 space-y-6"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-text-primary truncate max-w-xs">{data.filename}</h3>
          <div className="flex items-center gap-3 mt-1">
            <StatusBadge status={data.status} />
            {data.duration_sec && (
              <span className="badge bg-bg-tertiary text-text-secondary border border-border">
                {formatDuration(data.duration_sec)}
              </span>
            )}
            {data.fps && (
              <span className="badge bg-bg-tertiary text-text-secondary border border-border">
                {data.fps} fps
              </span>
            )}
          </div>
        </div>
      </div>

      <PipelineStepper status={data.status} />

      {data.status === "done" && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="pt-4 border-t border-border space-y-6"
        >
          <div>
            <p className="text-sm font-medium text-text-secondary mb-3">Generate highlight reel</p>
            <HighlightRequestForm matchId={matchId} onJobCreated={handleJobCreated} />
          </div>

          {jobs.length > 0 && (
            <div>
              <p className="text-xs text-text-muted mb-3 uppercase tracking-wider font-semibold">
                Generated highlights
              </p>
              <HighlightJobsList jobs={jobs} onJobDeleted={handleJobDeleted} />
            </div>
          )}
        </motion.div>
      )}

      {data.status === "failed" && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-red-500/5 border border-red-500/20 text-accent-red">
          <AlertCircle size={18} />
          <p className="text-sm">Processing failed. Please re-upload the match.</p>
        </div>
      )}
    </motion.div>
  )
}
