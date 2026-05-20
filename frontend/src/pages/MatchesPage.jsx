import { useState, useEffect, useRef } from "react"
import { useLocation } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import { ListVideo, X } from "lucide-react"
import toast from "react-hot-toast"
import PageWrapper from "../components/layout/PageWrapper"
import Sidebar from "../components/layout/Sidebar"
import MatchStatusCard from "../components/match/MatchStatusCard"
import JobStatusCard from "../components/match/JobStatusCard"
import EmptyState from "../components/ui/EmptyState"
import UploadZone from "../components/upload/UploadZone"
import { deleteMatch } from "../lib/api"

const STORAGE_KEY = "hl_matches"

function loadMatches() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]")
  } catch {
    return []
  }
}

function saveMatches(list) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
}

export default function MatchesPage() {
  const location = useLocation()
  const [matches, setMatches] = useState(loadMatches)
  const [selectedId, setSelectedId] = useState(null)
  const [activeJobId, setActiveJobId] = useState(null)
  const [showUploadDrawer, setShowUploadDrawer] = useState(false)
  const [deleteIds, setDeleteIds] = useState(new Set())
  const [deleteLoading, setDeleteLoading] = useState(false)
  const detailRef = useRef(null)

  useEffect(() => {
    if (location.state?.matchId) {
      const { matchId, filename } = location.state
      addMatch(matchId, filename)
      setSelectedId(matchId)
    }
  }, [location.state])

  const addMatch = (matchId, filename) => {
    setMatches((prev) => {
      if (prev.some((m) => m.match_id === matchId)) return prev
      const updated = [
        { match_id: matchId, filename: filename ?? matchId, status: "uploaded", uploadedAt: new Date().toISOString() },
        ...prev,
      ]
      saveMatches(updated)
      return updated
    })
  }

  const handleSelect = (id) => {
    setSelectedId(id)
    setActiveJobId(null)
    setTimeout(() => detailRef.current?.scrollIntoView({ behavior: "smooth" }), 100)
  }

  const handleToggleDelete = (matchId) => {
    setDeleteIds((prev) => {
      const next = new Set(prev)
      if (next.has(matchId)) next.delete(matchId)
      else next.add(matchId)
      return next
    })
  }

  const handleDeleteConfirm = async () => {
    setDeleteLoading(true)
    const ids = [...deleteIds]
    const results = await Promise.allSettled(ids.map((id) => deleteMatch(id)))

    const succeeded = []
    const failed = []
    results.forEach((r, i) => {
      if (r.status === "fulfilled") succeeded.push(ids[i])
      else failed.push(ids[i])
    })

    if (succeeded.length > 0) {
      setMatches((prev) => {
        const updated = prev.filter((m) => !succeeded.includes(m.match_id))
        saveMatches(updated)
        return updated
      })
      if (succeeded.includes(selectedId)) {
        setSelectedId(null)
        setActiveJobId(null)
      }
      toast.success(`Deleted ${succeeded.length} match${succeeded.length > 1 ? "es" : ""}`)
    }

    if (failed.length > 0) {
      toast.error(`${failed.length} match${failed.length > 1 ? "es" : ""} could not be deleted (may still be processing)`)
    }

    setDeleteIds(new Set())
    setDeleteLoading(false)
  }

  const handleUploadSuccess = (matchId, filename) => {
    addMatch(matchId, filename)
    setSelectedId(matchId)
    setActiveJobId(null)
    setShowUploadDrawer(false)
  }

  const handleJobCreated = (jobId) => {
    setActiveJobId(jobId)
  }

  return (
    <PageWrapper>
      <div className="pt-16 min-h-screen">
        <div className="max-w-7xl mx-auto px-6 py-8 flex gap-8">
          <div className="hidden md:block">
            <Sidebar
              matches={matches}
              selectedId={selectedId}
              onSelect={handleSelect}
              onUploadClick={() => setShowUploadDrawer(true)}
              deleteIds={deleteIds}
              onToggleDelete={handleToggleDelete}
              onDeleteConfirm={handleDeleteConfirm}
              deleteLoading={deleteLoading}
            />
          </div>

          <main ref={detailRef} className="flex-1 min-w-0 space-y-6">
            {selectedId ? (
              <AnimatePresence mode="wait">
                <motion.div
                  key={selectedId}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                  className="space-y-6"
                >
                  <MatchStatusCard matchId={selectedId} onJobCreated={handleJobCreated} />
                  {activeJobId && <JobStatusCard jobId={activeJobId} />}
                </motion.div>
              </AnimatePresence>
            ) : (
              <EmptyState
                icon={ListVideo}
                title="No match selected"
                description="Select a match from the sidebar or upload a new one to get started."
                action={{ label: "Upload Match", onClick: () => setShowUploadDrawer(true) }}
              />
            )}
          </main>
        </div>
      </div>

      <AnimatePresence>
        {showUploadDrawer && (
          <motion.div
            key="drawer"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-6"
            onClick={() => setShowUploadDrawer(false)}
          >
            <motion.div
              initial={{ scale: 0.95, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 20 }}
              className="glass-card p-8 w-full max-w-2xl space-y-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-text-primary">Upload New Match</h2>
                <button className="btn-ghost p-1" onClick={() => setShowUploadDrawer(false)}>
                  <X size={18} />
                </button>
              </div>
              <UploadZone onUploadSuccess={handleUploadSuccess} />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </PageWrapper>
  )
}
