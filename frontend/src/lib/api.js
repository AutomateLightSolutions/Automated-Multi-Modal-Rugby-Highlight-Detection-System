import axios from "axios"

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1",
  timeout: 30000,
})

export const uploadMatch = (file, onProgress) => {
  const form = new FormData()
  form.append("file", file)
  return api.post("/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 0, // no timeout — large video files can take minutes to upload
    onUploadProgress: (e) => {
      const pct = Math.round((e.loaded * 100) / e.total)
      onProgress?.(pct)
    },
  })
}

export const listMatches = () =>
  api.get("/matches")

export const getMatchStatus = (matchId) =>
  api.get(`/matches/${matchId}/status`)

export const deleteMatch = (matchId) =>
  api.delete(`/matches/${matchId}`)

export const generateHighlight = (matchId, highlightType, requestedEvents) =>
  api.post("/highlights/generate", {
    match_id: matchId,
    highlight_type: highlightType,
    requested_events: requestedEvents,
  })

export const getJobStatus = (jobId) =>
  api.get(`/highlights/status/${jobId}`)

export const getMatchHighlights = (matchId) =>
  api.get(`/matches/${matchId}/highlights`)

export const deleteHighlight = (jobId) =>
  api.delete(`/highlights/${jobId}`)

export const getStorageStatus = (matchId) =>
  api.get(`/highlights/storage/${matchId}`)

export const downloadHighlight = (jobId) =>
  `${api.defaults.baseURL}/highlights/download/${jobId}`

export const adminListMatches = () =>
  api.get("/admin/matches")

export const adminGetMatch = (matchId) =>
  api.get(`/admin/matches/${matchId}`)

export const adminGetTimeline = (matchId, fusionRunId) =>
  api.get(`/admin/matches/${matchId}/timeline`, {
    params: fusionRunId ? { fusion_run_id: fusionRunId } : {},
  })

export const adminVideoUrl = (matchId) =>
  `${api.defaults.baseURL}/admin/matches/${matchId}/video`

export const uploadModel = (module, modelFile, lexiconFile, onProgress) => {
  const form = new FormData()
  form.append("module", module)
  form.append("model_file", modelFile)
  if (lexiconFile) form.append("lexicon_file", lexiconFile)
  return api.post("/admin/models/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 0, // no timeout — checkpoint files can be several hundred MB
    onUploadProgress: (e) => {
      const pct = Math.round((e.loaded * 100) / e.total)
      onProgress?.(pct)
    },
  })
}

export const getModelStatus = () =>
  api.get("/admin/models/status")

export default api
