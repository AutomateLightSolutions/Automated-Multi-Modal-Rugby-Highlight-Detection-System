export const formatDuration = (seconds) => {
  if (seconds == null) return "—"
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}h ${m}m ${s}s`
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`
}

export const formatFileSize = (bytes) => {
  if (bytes == null) return "—"
  if (bytes >= 1_073_741_824) return `${(bytes / 1_073_741_824).toFixed(1)} GB`
  if (bytes >= 1_048_576) return `${(bytes / 1_048_576).toFixed(0)} MB`
  return `${(bytes / 1024).toFixed(0)} KB`
}

export const formatConfidence = (value) => {
  if (value == null) return "—"
  return `${Math.round(value * 100)}%`
}

export const formatTimeAgo = (isoString) => {
  if (!isoString) return "—"
  const diff = (Date.now() - new Date(isoString).getTime()) / 1000
  if (diff < 60) return "just now"
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

export const formatMatchTime = (seconds) => {
  if (seconds == null) return "00:00"
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`
}
