import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Download, AlertCircle, CheckCircle, Loader2 } from "lucide-react"
import toast from "react-hot-toast"
import { useJobPolling } from "../../hooks/useJobPolling"
import { downloadHighlight } from "../../lib/api"
import LoadingSpinner from "../ui/LoadingSpinner"
import SegmentsTable from "./SegmentsTable"
import Timeline from "../ui/Timeline"

function ModulePill({ label }) {
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium
      bg-indigo-500/10 border border-indigo-500/20 text-accent-indigo">
      <span className="w-1.5 h-1.5 rounded-full bg-accent-indigo animate-pulse" />
      {label}
    </span>
  )
}

function SkeletonRows() {
  return (
    <div className="space-y-2 mt-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-12 rounded-xl bg-gradient-to-r from-bg-tertiary via-bg-hover to-bg-tertiary bg-[length:200%_100%] animate-shimmer" />
      ))}
    </div>
  )
}

export default function JobStatusCard({ jobId }) {
  const { data, isLoading } = useJobPolling(jobId)
  const [preparing, setPreparing] = useState(false)

  const handleDownload = () => {
    setPreparing(true)
    toast.success("✨ Highlight ready to download!")
    setTimeout(() => {
      window.open(downloadHighlight(jobId), "_blank")
      setPreparing(false)
    }, 800)
  }

  if (isLoading || !data) {
    return (
      <div className="glass-card p-6">
        <LoadingSpinner text="Starting job…" />
      </div>
    )
  }

  return (
    <AnimatePresence mode="wait">
      {data.status === "running" && (
        <motion.div
          key="running"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6 space-y-5"
        >
          <div className="flex items-center gap-3">
            <Loader2 size={20} className="animate-spin text-accent-indigo" />
            <p className="font-semibold text-text-primary">Analysing your match…</p>
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
        </motion.div>
      )}

      {data.status === "done" && (
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
                  {data.segments?.length ?? 0} segments selected
                </p>
              </div>
            </div>

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
          </div>

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
          <div className="flex items-start gap-3">
            <AlertCircle size={20} className="text-accent-red mt-0.5" />
            <div>
              <p className="font-semibold text-accent-red">Highlight generation failed</p>
              <p className="text-sm text-text-secondary mt-1">
                {data.error_message ?? "An unknown error occurred."}
              </p>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
