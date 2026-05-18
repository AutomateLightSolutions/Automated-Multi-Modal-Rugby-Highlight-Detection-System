import { useCallback, useState, useRef } from "react"
import { useDropzone } from "react-dropzone"
import { motion, AnimatePresence } from "framer-motion"
import { Volleyball, Upload, AlertCircle, CheckCircle, RefreshCw } from "lucide-react"
import toast from "react-hot-toast"
import { uploadMatch } from "../../lib/api"
import ProgressBar from "../ui/ProgressBar"
import { formatFileSize } from "../../utils/formatters"

const MAX_SIZE = 10 * 1024 * 1024 * 1024

export default function UploadZone({ onUploadSuccess }) {
  const [state, setState] = useState("idle") // idle | uploading | processing | error
  const [progress, setProgress] = useState(0)
  const [file, setFile] = useState(null)
  const [speed, setSpeed] = useState(0)
  const [error, setError] = useState("")
  const startTime = useRef(null)
  const lastLoaded = useRef(0)

  const handleProgress = useCallback((pct) => {
    setProgress(pct)
    const elapsed = (Date.now() - startTime.current) / 1000
    if (elapsed > 0 && file) {
      const bytesUploaded = (pct / 100) * file.size
      const diff = bytesUploaded - lastLoaded.current
      lastLoaded.current = bytesUploaded
      setSpeed(diff / elapsed)
    }
  }, [file])

  const onDrop = useCallback(async (accepted, rejected) => {
    if (rejected.length > 0) {
      setError("Only .mp4 and .mov files are accepted.")
      setState("error")
      return
    }
    if (!accepted.length) return

    const f = accepted[0]
    setFile(f)
    setState("uploading")
    setProgress(0)
    startTime.current = Date.now()
    lastLoaded.current = 0
    toast(`Uploading ${f.name}…`)

    try {
      const res = await uploadMatch(f, handleProgress)
      setState("processing")
      toast.success("Match uploaded successfully")
      onUploadSuccess?.(res.data.match_id, res.data.filename)
    } catch (err) {
      const msg = err?.response?.data?.detail ?? err.message ?? "Upload failed"
      setError(msg)
      setState("error")
      toast.error(msg)
    }
  }, [handleProgress, onUploadSuccess])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "video/mp4": [".mp4"], "video/quicktime": [".mov"] },
    maxSize: MAX_SIZE,
    multiple: false,
    disabled: state === "uploading" || state === "processing",
  })

  const reset = () => {
    setState("idle")
    setFile(null)
    setProgress(0)
    setError("")
  }

  const truncate = (name, n = 30) =>
    name.length > n ? name.slice(0, n - 1) + "…" : name

  let borderCls = "border-border hover:border-border-light hover:bg-bg-tertiary/50"
  if (isDragActive) borderCls = "border-accent-indigo bg-indigo-500/10 scale-[1.02]"
  else if (state === "error") borderCls = "border-accent-red bg-red-500/5"
  else if (state === "processing") borderCls = "border-accent-emerald bg-emerald-500/5 animate-pulse-slow"

  return (
    <div
      {...getRootProps()}
      className={`relative min-h-[280px] rounded-3xl border-2 border-dashed transition-all duration-300 flex flex-col items-center justify-center p-8 cursor-pointer ${borderCls}`}
    >
      <input {...getInputProps()} />

      {(isDragActive || state === "idle") && (
        <AnimatePresence mode="wait">
          {isDragActive ? (
            <motion.div
              key="drag"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="flex flex-col items-center gap-4"
            >
              <div className="p-5 rounded-2xl bg-indigo-500/20 shadow-glow-indigo text-accent-indigo">
                <Upload size={40} />
              </div>
              <p className="text-lg font-semibold text-accent-indigo">Drop it here!</p>
            </motion.div>
          ) : (
            <motion.div
              key="idle"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center gap-5"
            >
              <motion.div
                className="p-5 rounded-2xl bg-indigo-500/10 shadow-glow-indigo text-accent-indigo"
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
              >
                <Volleyball size={48} />
              </motion.div>
              <div className="text-center space-y-1">
                <p className="text-lg font-semibold text-text-primary">
                  Drag &amp; drop your match video
                </p>
                <p className="text-sm text-text-secondary">
                  or <span className="text-accent-indigo underline">browse files</span>
                </p>
              </div>
              <div className="flex gap-2">
                {[".mp4", ".mov"].map((ext) => (
                  <span key={ext} className="badge-indigo">{ext}</span>
                ))}
                <span className="badge bg-bg-tertiary text-text-muted border border-border">
                  Up to 10 GB
                </span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      )}

      {state === "uploading" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md space-y-4"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-indigo-500/10 text-accent-indigo">
              <Upload size={20} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">
                {truncate(file?.name ?? "")}
              </p>
              <p className="text-xs text-text-muted">
                {formatFileSize(file?.size)} · {formatFileSize(speed)}/s
              </p>
            </div>
            <span className="text-sm font-mono text-accent-indigo">{progress}%</span>
          </div>
          <ProgressBar value={progress} color="indigo" animated />
        </motion.div>
      )}

      {state === "processing" && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center gap-4"
        >
          <div className="p-5 rounded-2xl bg-emerald-500/10 shadow-glow-cyan text-accent-emerald">
            <CheckCircle size={40} />
          </div>
          <div className="text-center">
            <p className="text-lg font-semibold text-text-primary">Video received</p>
            <p className="text-sm text-text-secondary">Processing started — tracking below</p>
          </div>
        </motion.div>
      )}

      {state === "error" && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center gap-4"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="p-5 rounded-2xl bg-red-500/10 text-accent-red">
            <AlertCircle size={40} />
          </div>
          <div className="text-center">
            <p className="text-lg font-semibold text-text-primary">Upload failed</p>
            <p className="text-sm text-accent-red">{error}</p>
          </div>
          <button className="btn-secondary flex items-center gap-2" onClick={reset}>
            <RefreshCw size={14} />
            Try Again
          </button>
        </motion.div>
      )}
    </div>
  )
}
