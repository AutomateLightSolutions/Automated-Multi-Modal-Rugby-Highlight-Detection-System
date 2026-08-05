import { useCallback, useEffect, useState } from "react"
import { motion } from "framer-motion"
import { UploadCloud, FileArchive, FileJson, CheckCircle2, XCircle } from "lucide-react"
import toast from "react-hot-toast"
import PageWrapper from "../components/layout/PageWrapper"
import LoadingSpinner from "../components/ui/LoadingSpinner"
import ProgressBar from "../components/ui/ProgressBar"
import { MODULES } from "../constants/models"
import { uploadModel, getModelStatus } from "../lib/api"
import { formatFileSize, formatTimeAgo } from "../utils/formatters"

function StatusRow({ module, label, status }) {
  return (
    <div className="flex items-center justify-between px-4 py-3 border-b border-border last:border-0">
      <div>
        <p className="text-sm font-medium text-text-primary">{label}</p>
        <p className="text-xs text-text-muted font-mono">{module}</p>
      </div>
      <div className="flex items-center gap-6 text-xs">
        <div className="flex items-center gap-1.5">
          {status?.model_installed ? (
            <CheckCircle2 size={14} className="text-accent-emerald" />
          ) : (
            <XCircle size={14} className="text-text-muted" />
          )}
          <span className="text-text-secondary">
            Model{status?.uploaded_at ? ` — ${formatTimeAgo(status.uploaded_at)}` : ""}
          </span>
        </div>
        {module === "commentary" && (
          <div className="flex items-center gap-1.5">
            {status?.lexicon_installed ? (
              <CheckCircle2 size={14} className="text-accent-emerald" />
            ) : (
              <XCircle size={14} className="text-text-muted" />
            )}
            <span className="text-text-secondary">
              Lexicon{status?.lexicon_uploaded_at ? ` — ${formatTimeAgo(status.lexicon_uploaded_at)}` : ""}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

export default function AdminModelsPage() {
  const [status, setStatus] = useState(null)
  const [statusLoading, setStatusLoading] = useState(true)

  const [module, setModule] = useState("commentary")
  const [modelFile, setModelFile] = useState(null)
  const [lexiconFile, setLexiconFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)

  const refreshStatus = useCallback(() => {
    setStatusLoading(true)
    getModelStatus()
      .then((res) => setStatus(res.data.modules))
      .catch(() => toast.error("Failed to load model status"))
      .finally(() => setStatusLoading(false))
  }, [])

  useEffect(() => {
    refreshStatus()
  }, [refreshStatus])

  const isCommentary = module === "commentary"

  const handleModuleChange = (e) => {
    setModule(e.target.value)
    setLexiconFile(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!modelFile) {
      toast.error("Select a model .zip file first.")
      return
    }
    if (isCommentary && !lexiconFile) {
      toast.error("A lexicon.json file is required for the commentary module.")
      return
    }

    setUploading(true)
    setProgress(0)
    try {
      await uploadModel(module, modelFile, isCommentary ? lexiconFile : null, setProgress)
      toast.success(`Model installed for '${module}'.`)
      setModelFile(null)
      setLexiconFile(null)
      refreshStatus()
    } catch (err) {
      const msg = err?.response?.data?.detail ?? err.message ?? "Upload failed"
      toast.error(msg)
    } finally {
      setUploading(false)
    }
  }

  return (
    <PageWrapper>
      <div className="pt-16 min-h-screen">
        <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">
          <div>
            <h1 className="text-2xl font-semibold text-text-primary">Admin — Models</h1>
            <p className="text-sm text-text-secondary mt-1">
              Upload a trained model checkpoint (zip) for a module. Commentary also
              requires a lexicon.json.
            </p>
          </div>

          <div className="glass-card rounded-xl border border-border overflow-hidden">
            <div className="px-4 py-3 border-b border-border bg-bg-secondary">
              <p className="text-xs uppercase tracking-wider text-text-muted font-medium">
                Current status
              </p>
            </div>
            {statusLoading ? (
              <div className="p-6"><LoadingSpinner text="Loading status…" /></div>
            ) : (
              MODULES.map((m) => (
                <StatusRow key={m.value} module={m.value} label={m.label} status={status?.[m.value]} />
              ))
            )}
          </div>

          <form onSubmit={handleSubmit} className="glass-card rounded-xl border border-border p-6 space-y-5">
            <div>
              <label htmlFor="module-select" className="block text-sm font-medium text-text-primary mb-1.5">
                Module
              </label>
              <select
                id="module-select"
                value={module}
                onChange={handleModuleChange}
                disabled={uploading}
                className="input w-full"
              >
                {MODULES.map((m) => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="model-file" className="block text-sm font-medium text-text-primary mb-1.5">
                Model (.zip)
              </label>
              <label
                htmlFor="model-file"
                className="flex items-center gap-3 rounded-xl border-2 border-dashed border-border hover:border-border-light px-4 py-4 cursor-pointer transition-colors"
              >
                <FileArchive size={20} className="text-accent-indigo shrink-0" />
                <span className="text-sm text-text-secondary truncate">
                  {modelFile ? `${modelFile.name} (${formatFileSize(modelFile.size)})` : "Choose a .zip file…"}
                </span>
                <input
                  id="model-file"
                  type="file"
                  accept=".zip"
                  className="hidden"
                  disabled={uploading}
                  onChange={(e) => setModelFile(e.target.files?.[0] ?? null)}
                />
              </label>
            </div>

            {isCommentary && (
              <div>
                <label htmlFor="lexicon-file" className="block text-sm font-medium text-text-primary mb-1.5">
                  Lexicon (.json)
                </label>
                <label
                  htmlFor="lexicon-file"
                  className="flex items-center gap-3 rounded-xl border-2 border-dashed border-border hover:border-border-light px-4 py-4 cursor-pointer transition-colors"
                >
                  <FileJson size={20} className="text-accent-cyan shrink-0" />
                  <span className="text-sm text-text-secondary truncate">
                    {lexiconFile ? `${lexiconFile.name} (${formatFileSize(lexiconFile.size)})` : "Choose a .json file…"}
                  </span>
                  <input
                    id="lexicon-file"
                    type="file"
                    accept=".json"
                    className="hidden"
                    disabled={uploading}
                    onChange={(e) => setLexiconFile(e.target.files?.[0] ?? null)}
                  />
                </label>
              </div>
            )}

            {uploading && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-2">
                <div className="flex justify-between text-xs text-text-muted">
                  <span>Uploading…</span>
                  <span className="font-mono text-accent-indigo">{progress}%</span>
                </div>
                <ProgressBar value={progress} color="indigo" animated />
              </motion.div>
            )}

            <button type="submit" disabled={uploading} className="btn-primary w-full flex items-center justify-center gap-2">
              <UploadCloud size={16} />
              {uploading ? "Uploading…" : "Upload"}
            </button>
          </form>
        </div>
      </div>
    </PageWrapper>
  )
}
