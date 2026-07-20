import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  Download, AlertCircle, AlertTriangle, CheckCircle, Loader2,
  Trash2, ChevronDown, ChevronUp, Play,
} from "lucide-react"
import toast from "react-hot-toast"
import { useJobPolling } from "../../hooks/useJobPolling"
import { downloadHighlight, deleteHighlight } from "../../lib/api"
import LoadingSpinner from "../ui/LoadingSpinner"
import SegmentsTable from "./SegmentsTable"
import Timeline from "../ui/Timeline"
import { EVENT_TYPE_LABELS, HIGHLIGHT_TYPES } from "../../constants/highlights"

function highlightTypeLabel(value) {
  return HIGHLIGHT_TYPES.find((h) => h.value === value)?.label ?? value
}

function ModulePill({ label }) {
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium
      bg-indigo-500/10 border border-indigo-500/20 text-accent-indigo">
      <span className="w-1.5 h-1.5 rounded-full bg-accent-indigo animate-pulse" />
      {label}
    </span>
  )
}

function DeleteControl({ onConfirm, deleting }) {
  const [pending, setPending] = useState(false)

  if (pending) {
    return (
      <div
        onClick={(e) => e.stopPropagation()}
        className="flex items-center gap-2 text-xs"
      >
        <AlertTriangle size={13} className="text-red-400 shrink-0" />
        <span className="text-text-muted">Delete this highlight?</span>
        <button
          onClick={() => setPending(false)}
          disabled={deleting}
          className="btn-ghost px-2 py-1 text-xs disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          onClick={onConfirm}
          disabled={deleting}
          className="px-2 py-1 text-xs bg-red-500/20 border border-red-500/40 text-red-400
                     rounded-lg hover:bg-red-500/30 transition-colors disabled:opacity-50"
        >
          {deleting ? "Deleting…" : "Yes, delete"}
        </button>
      </div>
    )
  }

  return (
    <button
      onClick={(e) => { e.stopPropagation(); setPending(true) }}
      title="Delete highlight"
      className="shrink-0 p-1.5 rounded-lg text-text-muted hover:text-red-400 hover:bg-red-500/10 transition-all"
    >
      <Trash2 size={14} />
    </button>
  )
}

export default function JobStatusCard({ jobId, isLatest = true, onDeleted }) {
  const { data, isLoading } = useJobPolling(jobId)
  const [preparing, setPreparing] = useState(false)
  const [expanded, setExpanded] = useState(isLatest)
  const [showPreview, setShowPreview] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const handleDownload = () => {
    setPreparing(true)
    toast.success("✨ Highlight ready to download!")
    setTimeout(() => {
      window.open(downloadHighlight(jobId), "_blank")
      setPreparing(false)
    }, 800)
  }

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await deleteHighlight(jobId)
      toast.success("Highlight deleted")
      onDeleted?.(jobId)
    } catch (err) {
      toast.error(err?.response?.data?.detail ?? "Failed to delete highlight")
    } finally {
      setDeleting(false)
    }
  }

  if (isLoading || !data) {
    return (
      <div className="glass-card p-6">
        <LoadingSpinner text="Starting job…" />
      </div>
    )
  }

  const eventBadges = data.requested_events ?? []

  return (
    <AnimatePresence mode="wait">
      {data.status === "running" && (
        <motion.div
          key="running"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6 space-y-5"
        >
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <Loader2 size={20} className="animate-spin text-accent-indigo" />
              <p className="font-semibold text-text-primary">Analysing your match…</p>
            </div>
            <DeleteControl onConfirm={handleDelete} deleting={deleting} />
          </div>

          <div className="h-2 rounded-full overflow-hidden bg-bg-tertiary">
            <div
              className="h-full rounded-full bg-gradient-to-r from-accent-indigo to-accent-cyan"
              style={{
                width: "60%",
                background: "linear-gradient(90deg, #6366F1 0%, #06B6D4 50%, #10B981 100%)",
                backgroundSize: "200% 100%",
                animation: "shimmer 2s linear infinite",
              }}
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <ModulePill label="Visual Analysis" />
            <ModulePill label="Commentary" />
            <ModulePill label="Audio Energy" />
          </div>

          {(data.highlight_type || eventBadges.length > 0) && (
            <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-border">
              <span className="text-xs text-text-muted uppercase tracking-wider font-semibold">Request</span>
              {data.highlight_type && (
                <span className="badge-amber text-xs">{highlightTypeLabel(data.highlight_type)}</span>
              )}
              {eventBadges.map((ev) => (
                <span key={ev} className="badge-cyan text-xs">{EVENT_TYPE_LABELS[ev] ?? ev}</span>
              ))}
            </div>
          )}
        </motion.div>
      )}

      {data.status === "done" && !expanded && (
        <motion.button
          key="done-collapsed"
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          onClick={() => setExpanded(true)}
          className="w-full flex items-center justify-between gap-3 p-4 rounded-2xl border border-border
                     bg-bg-card hover:border-border-light hover:bg-bg-hover transition-all text-left"
        >
          <div className="flex items-center gap-3 min-w-0">
            <CheckCircle size={16} className="text-accent-emerald shrink-0" />
            <span className="text-sm font-medium text-text-primary truncate">
              {highlightTypeLabel(data.highlight_type)} · {eventBadges.map((ev) => EVENT_TYPE_LABELS[ev] ?? ev).join(", ")}
            </span>
            <span className="text-xs text-text-muted shrink-0">
              {data.segments?.length ?? 0} clips
            </span>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <DeleteControl onConfirm={handleDelete} deleting={deleting} />
            <ChevronDown size={14} className="text-text-muted" />
          </div>
        </motion.button>
      )}

      {data.status === "done" && expanded && (
        <motion.div
          key="done"
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-card p-6 space-y-6"
        >
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-3">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", stiffness: 260, damping: 20 }}
                className="p-2 rounded-xl bg-emerald-500/10 text-accent-emerald"
              >
                <CheckCircle size={22} />
              </motion.div>
              <div>
                <p className="font-semibold text-text-primary">Highlight Ready</p>
                <p className="text-xs text-text-secondary">
                  {highlightTypeLabel(data.highlight_type)} · {data.segments?.length ?? 0} segments selected
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                className="btn-secondary flex items-center gap-2"
                onClick={() => setShowPreview((v) => !v)}
              >
                <Play size={15} /> {showPreview ? "Hide preview" : "Preview"}
              </button>
              <button
                className="btn-primary flex items-center gap-2"
                onClick={handleDownload}
                disabled={preparing}
              >
                {preparing ? (
                  <><Loader2 size={15} className="animate-spin" /> Preparing…</>
                ) : (
                  <><Download size={15} /> Download Highlight</>
                )}
              </button>
              <DeleteControl onConfirm={handleDelete} deleting={deleting} />
              {!isLatest && (
                <button
                  onClick={() => setExpanded(false)}
                  title="Collapse"
                  className="shrink-0 p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-tertiary transition-all"
                >
                  <ChevronUp size={16} />
                </button>
              )}
            </div>
          </div>

          {eventBadges.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {eventBadges.map((ev) => (
                <span key={ev} className="badge-cyan text-xs">{EVENT_TYPE_LABELS[ev] ?? ev}</span>
              ))}
            </div>
          )}

          {showPreview && (
            <video
              controls
              preload="none"
              src={downloadHighlight(jobId)}
              className="w-full rounded-xl border border-border bg-black"
            />
          )}

          {data.segments?.length > 0 && (
            <>
              <div className="pt-2 border-t border-border">
                <p className="text-xs text-text-muted mb-3 uppercase tracking-wider font-semibold">
                  Match Timeline
                </p>
                <Timeline segments={data.segments} />
              </div>
              <div className="pt-2 border-t border-border">
                <p className="text-xs text-text-muted mb-3 uppercase tracking-wider font-semibold">
                  Segments
                </p>
                <SegmentsTable segments={data.segments} />
              </div>
            </>
          )}
        </motion.div>
      )}

      {data.status === "failed" && (
        <motion.div
          key="failed"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-5 border border-red-500/20 bg-red-500/5"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-3">
              <AlertCircle size={20} className="text-accent-red mt-0.5" />
              <div>
                <p className="font-semibold text-accent-red">Highlight generation failed</p>
                <p className="text-sm text-text-secondary mt-1">
                  {data.error_message ?? "An unknown error occurred."}
                </p>
              </div>
            </div>
            <DeleteControl onConfirm={handleDelete} deleting={deleting} />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
