import { useState, useEffect, useRef } from "react"
import { useLocation } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import { ListVideo, X } from "lucide-react"
import toast from "react-hot-toast"
import PageWrapper from "../components/layout/PageWrapper"
import Sidebar from "../components/layout/Sidebar"
import MatchStatusCard from "../components/match/MatchStatusCard"
import EmptyState from "../components/ui/EmptyState"
import UploadZone from "../components/upload/UploadZone"
import { deleteMatch, listMatches } from "../lib/api"

function toSidebarMatch(m) {
  return {
    match_id: m.match_id,
    filename: m.filename,
    status: m.status,
    uploadedAt: m.created_at,
  }
}

export default function MatchesPage() {
  const location = useLocation()
  const [matches, setMatches] = useState([])
  const [matchesLoading, setMatchesLoading] = useState(true)
  const [selectedId, setSelectedId] = useState(null)
  const [showUploadDrawer, setShowUploadDrawer] = useState(false)
  const [deleteLoading, setDeleteLoading] = useState(false)
  const detailRef = useRef(null)

  useEffect(() => {
    listMatches()
      .then((res) => setMatches(res.data.map(toSidebarMatch)))
      .catch(() => toast.error("Failed to load matches"))
      .finally(() => setMatchesLoading(false))
  }, [])

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
      return [
        { match_id: matchId, filename: filename ?? matchId, status: "uploaded", uploadedAt: new Date().toISOString() },
        ...prev,
      ]
    })
  }

  const handleSelect = (id) => {
    setSelectedId(id)
    setTimeout(() => detailRef.current?.scrollIntoView({ behavior: "smooth" }), 100)
  }

  const handleDeleteMatch = async (matchId) => {
    setDeleteLoading(true)
    try {
      await deleteMatch(matchId)
      toast.success("Match deleted")
    } catch (err) {
      if (err?.response?.status === 404) {
        // Already gone on the backend (e.g. stale local cache after a DB reset) —
        // still remove it from the visible list instead of leaving it stuck.
        toast("Match was already removed", { icon: "ℹ️" })
      } else {
        toast.error(err?.response?.data?.detail ?? "Failed to delete match")
        setDeleteLoading(false)
        return
      }
    }

    setMatches((prev) => prev.filter((m) => m.match_id !== matchId))
    if (matchId === selectedId) {
      setSelectedId(null)
    }
    setDeleteLoading(false)
  }

  const handleUploadSuccess = (matchId, filename) => {
    addMatch(matchId, filename)
    setSelectedId(matchId)
    setShowUploadDrawer(false)
  }

  const handleStatusChange = (matchId, status) => {
    setMatches((prev) =>
      prev.map((m) => (m.match_id === matchId ? { ...m, status } : m))
    )
  }

  return (
    <PageWrapper>
      <div className="pt-16 min-h-screen">
        <div className="max-w-7xl mx-auto px-6 py-8 flex gap-8">
          <div className="hidden md:block">
            <Sidebar
              matches={matches}
              loading={matchesLoading}
              selectedId={selectedId}
              onSelect={handleSelect}
              onUploadClick={() => setShowUploadDrawer(true)}
              onDeleteMatch={handleDeleteMatch}
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
                  <MatchStatusCard
                    matchId={selectedId}
                    onStatusChange={(status) => handleStatusChange(selectedId, status)}
                  />
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
