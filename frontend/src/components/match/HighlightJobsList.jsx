import { AnimatePresence, motion } from "framer-motion"
import JobStatusCard from "./JobStatusCard"

export default function HighlightJobsList({ jobs, onJobDeleted }) {
  if (jobs.length === 0) return null

  return (
    <div className="space-y-3">
      <AnimatePresence initial={false}>
        {jobs.map((job, index) => (
          <motion.div
            key={job.job_id}
            layout
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97 }}
          >
            <JobStatusCard
              jobId={job.job_id}
              isLatest={index === 0}
              onDeleted={onJobDeleted}
            />
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
