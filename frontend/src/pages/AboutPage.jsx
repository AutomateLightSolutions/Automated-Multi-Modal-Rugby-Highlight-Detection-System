import { motion } from "framer-motion"
import { ArrowRight } from "lucide-react"
import PageWrapper from "../components/layout/PageWrapper"

const PIPELINE_NODES = [
  { label: "Upload", color: "border-accent-indigo text-accent-indigo" },
  { label: "FFmpeg\nExtraction", color: "border-accent-cyan text-accent-cyan" },
  { label: "Visual\nModule", color: "border-accent-purple text-accent-purple" },
  { label: "Commentary\nModule", color: "border-accent-indigo text-accent-indigo" },
  { label: "Audio\nModule", color: "border-accent-emerald text-accent-emerald" },
  { label: "Fusion\nEngine", color: "border-accent-amber text-accent-amber" },
  { label: "NMS\nSelection", color: "border-accent-cyan text-accent-cyan" },
  { label: "Video\nAssembly", color: "border-accent-emerald text-accent-emerald" },
]

const TEAM = [
  {
    initials: "TD",
    name: "Thimira Deshaka",
    role: "Visual Analysis Module",
    desc: "Deep learning-based action recognition using ResNet/ViT for rugby event detection.",
    stack: ["PyTorch", "ResNet", "ViT", "OpenCV"],
    gradient: "from-indigo-500 to-purple-500",
  },
  {
    initials: "PY",
    name: "Piyushan",
    role: "Commentary Analysis Module",
    desc: "Whisper ASR transcription and rugby-specific NLP keyword scoring pipeline.",
    stack: ["Whisper", "NLP", "FastAPI"],
    gradient: "from-cyan-500 to-indigo-500",
  },
  {
    initials: "BH",
    name: "Bhashini",
    role: "Audio Energy Module",
    desc: "RMS energy and spectral analysis to detect crowd peaks and high-intensity moments.",
    stack: ["librosa", "NumPy", "Signal Processing"],
    gradient: "from-emerald-500 to-cyan-500",
  },
]

const TECH = [
  { name: "PyTorch",     color: "text-orange-400 border-orange-400/30 bg-orange-400/5" },
  { name: "FastAPI",     color: "text-emerald-400 border-emerald-400/30 bg-emerald-400/5" },
  { name: "Celery",      color: "text-green-400 border-green-400/30 bg-green-400/5" },
  { name: "Redis",       color: "text-red-400 border-red-400/30 bg-red-400/5" },
  { name: "PostgreSQL",  color: "text-blue-400 border-blue-400/30 bg-blue-400/5" },
  { name: "FFmpeg",      color: "text-yellow-400 border-yellow-400/30 bg-yellow-400/5" },
  { name: "Whisper",     color: "text-purple-400 border-purple-400/30 bg-purple-400/5" },
  { name: "React",       color: "text-cyan-400 border-cyan-400/30 bg-cyan-400/5" },
  { name: "Tailwind CSS", color: "text-sky-400 border-sky-400/30 bg-sky-400/5" },
]

export default function AboutPage() {
  return (
    <PageWrapper>
      <div className="pt-16 max-w-6xl mx-auto px-6 py-16 space-y-24">
        {/* Architecture */}
        <section>
          <h2 className="text-3xl font-bold text-text-primary mb-2">System Architecture</h2>
          <p className="text-text-secondary mb-10">
            End-to-end pipeline from raw video to downloadable highlight reel.
          </p>

          <div className="glass-card p-8 overflow-x-auto">
            <div className="flex flex-wrap items-center gap-2 min-w-max">
              {PIPELINE_NODES.map((node, i) => (
                <div key={i} className="flex items-center gap-2">
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.08 }}
                    className={`border rounded-xl px-4 py-3 text-xs font-semibold whitespace-pre-line text-center min-w-[80px] ${node.color} bg-bg-tertiary`}
                  >
                    {node.label}
                  </motion.div>
                  {i < PIPELINE_NODES.length - 1 && (
                    <ArrowRight size={16} className="text-text-muted shrink-0" />
                  )}
                </div>
              ))}
            </div>

            <div className="mt-6 flex items-center gap-4 flex-wrap text-xs text-text-muted">
              <span className="badge bg-indigo-500/10 text-accent-indigo border border-indigo-500/20">
                Celery Workers (concurrency=3)
              </span>
              <span className="badge bg-cyan-500/10 text-accent-cyan border border-cyan-500/20">
                Redis Message Broker
              </span>
              <span className="badge bg-amber-500/10 text-accent-amber border border-amber-500/20">
                PostgreSQL State Store
              </span>
            </div>
          </div>
        </section>

        {/* Team */}
        <section>
          <h2 className="text-3xl font-bold text-text-primary mb-2">The Team</h2>
          <p className="text-text-secondary mb-10">Final year research project — each member owns one AI module.</p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {TEAM.map((member, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.12 }}
                className="glass-card-hover p-6 space-y-4"
              >
                <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${member.gradient} flex items-center justify-center text-white text-xl font-extrabold`}>
                  {member.initials}
                </div>
                <div>
                  <h3 className="font-semibold text-text-primary">{member.name}</h3>
                  <p className="text-sm text-accent-indigo font-medium">{member.role}</p>
                  <p className="text-sm text-text-secondary mt-2">{member.desc}</p>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {member.stack.map((t) => (
                    <span key={t} className="badge bg-bg-tertiary text-text-muted border border-border text-[11px]">
                      {t}
                    </span>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Tech Stack */}
        <section>
          <h2 className="text-3xl font-bold text-text-primary mb-2">Technology Stack</h2>
          <p className="text-text-secondary mb-10">The tools powering every layer of the system.</p>

          <div className="flex flex-wrap gap-3">
            {TECH.map((t, i) => (
              <motion.div
                key={t.name}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.05 }}
                className={`glass-card px-5 py-3 font-semibold text-sm border ${t.color} hover:-translate-y-0.5 transition-transform cursor-default`}
              >
                {t.name}
              </motion.div>
            ))}
          </div>
        </section>
      </div>
    </PageWrapper>
  )
}
