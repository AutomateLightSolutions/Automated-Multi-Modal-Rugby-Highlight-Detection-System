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
    onUploadProgress: (e) => {
      const pct = Math.round((e.loaded * 100) / e.total)
      onProgress?.(pct)
    },
  })
}

export const getMatchStatus = (matchId) =>
  api.get(`/matches/${matchId}/status`)

export const generateHighlight = (matchId, userFilter = null) =>
  api.post("/highlights/generate", {
    match_id: matchId,
    user_filter: userFilter,
  })

export const getJobStatus = (jobId) =>
  api.get(`/highlights/status/${jobId}`)

export const getStorageStatus = (matchId) =>
  api.get(`/highlights/storage/${matchId}`)

export const downloadHighlight = (jobId) =>
  `${api.defaults.baseURL}/highlights/download/${jobId}`

export default api
