import { useRef } from "react"
import { useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import { Zap, Clock, Target, Eye, Mic, Activity, ChevronDown, Upload } from "lucide-react"
import PageWrapper from "../components/layout/PageWrapper"
import StatCard from "../components/ui/StatCard"
import UploadZone from "../components/upload/UploadZone"

const STEPS = [
  {
    n: "01", icon: Upload, color: "text-accent-indigo",
    title: "Upload Match",
    desc: "Drop your full match video. We handle any length — up to 10 GB.",
  },
  {
    n: "02", icon: Eye, color: "text-accent-cyan",
    title: "AI Analysis",
    desc: "Three modules run in parallel: vision, commentary, and audio.",
  },
  {
    n: "03", icon: Zap, color: "text-accent-emerald",
    title: "Fusion Engine",
    desc: "Scores are fused and ranked. Non-max suppression removes duplicates.",
  },
  {
    n: "04", icon: Activity, color: "text-accent-amber",
    title: "Highlight Ready",
    desc: "Download a compact highlight reel in seconds.",
  },
]

const MODULES = [
  {
    Icon: Eye, color: "text-accent-cyan", glow: "shadow-glow-cyan", border: "border-t-accent-cyan",
    title: "Visual Analysis",
    desc: "Action recognition identifies scrums, tries, lineouts, tackles and more using deep computer vision.",
    badge: "ResNet / ViT",
  },
  {
    Icon: Mic, color: "text-accent-indigo", glow: "shadow-glow-indigo", border: "border-t-accent-indigo",
    title: "Commentary Analysis",
    desc: "Whisper ASR transcribes commentary and scores excitement from rugby-specific keyword detection.",
    badge: "OpenAI Whisper",
  },
  {
    Icon: Activity, color: "text-accent-emerald", glow: "", border: "border-t-accent-emerald",
    title: "Audio Energy",
    desc: "RMS energy analysis detects crowd excitement peaks and high-intensity moments acoustically.",
    badge: "Signal Processing",
  },
]

function GradientOrb({ className }) {
  return (
    <motion.div
      className={`absolute rounded-full blur-3xl pointer-events-none ${className}`}
      animate={{ x: [0, 20, -20, 0], y: [0, -20, 20, 0] }}
      transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
    />
  )
}

export default function HomePage() {
  const navigate = useNavigate()
  const uploadRef = useRef(null)

  const scrollToUpload = () =>
    uploadRef.current?.scrollIntoView({ behavior: "smooth" })

  const handleUploadSuccess = (matchId, filename) => {
    navigate("/matches", { state: { matchId, filename } })
  }

  return (
    <PageWrapper>
      <div className="pt-16">
        {/* HERO */}
        <section className="relative min-h-screen flex flex-col items-center justify-center px-6 overflow-hidden">
          <GradientOrb className="w-[600px] h-[600px] bg-indigo-600/8 -top-32 -left-32" />
          <GradientOrb className="w-[500px] h-[500px] bg-cyan-500/6 top-20 right-0" />
          <GradientOrb className="w-[400px] h-[400px] bg-emerald-500/5 bottom-0 left-1/3" />

          <div className="relative z-10 flex flex-col items-center text-center gap-8 max-w-4xl">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <span className="badge-indigo shadow-glow-indigo text-sm px-4 py-1.5">
                🏉 AI-Powered Sports Analytics
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="text-5xl md:text-7xl font-extrabold leading-tight tracking-tight"
            >
              Turn Full Matches Into
              <br />
              <span className="bg-hero-gradient bg-clip-text text-transparent">
                Instant Highlights
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="text-lg text-text-secondary max-w-2xl"
            >
              Multimodal AI analyses vision, commentary, and audio simultaneously
              to extract the most exciting moments from any rugby match.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="flex flex-wrap gap-4 justify-center"
            >
              <button className="btn-primary text-base px-8 py-4" onClick={scrollToUpload}>
                Get Started →
              </button>
              <button className="btn-secondary text-base px-8 py-4" onClick={() => navigate("/about")}>
                See How It Works
              </button>
            </motion.div>
          </div>

          <motion.div
            className="absolute bottom-10 text-text-muted"
            animate={{ y: [0, 6, 0] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          >
            <ChevronDown size={24} />
          </motion.div>
        </section>

        {/* STATS */}
        <section className="max-w-7xl mx-auto px-6 py-20">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <StatCard label="Vision · Commentary · Audio" value="3 AI Modules" icon={Zap} color="indigo" />
            <StatCard label="Processing time per match" value="< 40 min" icon={Clock} color="cyan" />
            <StatCard label="Event detection rate" value="90%+ Accuracy" icon={Target} color="emerald" />
          </div>
        </section>

        {/* HOW IT WORKS */}
        <section className="max-w-7xl mx-auto px-6 py-20">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-text-primary">How It Works</h2>
            <p className="text-text-secondary mt-3">Four steps from raw footage to highlight reel</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative">
            {STEPS.map((step, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="glass-card-hover p-6 flex flex-col gap-4"
              >
                <div className="flex items-center gap-3">
                  <span className="text-3xl font-extrabold bg-hero-gradient bg-clip-text text-transparent">
                    {step.n}
                  </span>
                  <div className={`p-2 rounded-xl bg-bg-tertiary ${step.color}`}>
                    <step.icon size={22} />
                  </div>
                </div>
                <div>
                  <h3 className="font-semibold text-text-primary">{step.title}</h3>
                  <p className="text-sm text-text-secondary mt-1">{step.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </section>

        {/* MODULES */}
        <section className="max-w-7xl mx-auto px-6 py-20">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-text-primary">
              Three Modules. One Highlight.
            </h2>
            <p className="text-text-secondary mt-3">
              Independent AI modules run concurrently, then fuse their scores.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {MODULES.map((mod, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
                className={`glass-card-hover p-6 border-t-2 ${mod.border} space-y-4`}
              >
                <motion.div
                  className={`p-3 rounded-xl bg-bg-tertiary ${mod.color} w-fit`}
                  animate={{ y: [0, -6, 0] }}
                  transition={{ duration: 3 + i, repeat: Infinity, ease: "easeInOut" }}
                >
                  <mod.Icon size={28} />
                </motion.div>
                <div>
                  <h3 className="font-semibold text-text-primary">{mod.title}</h3>
                  <p className="text-sm text-text-secondary mt-2">{mod.desc}</p>
                </div>
                <span className="badge-indigo text-xs">{mod.badge}</span>
              </motion.div>
            ))}
          </div>
        </section>

        {/* UPLOAD CTA */}
        <section ref={uploadRef} className="max-w-4xl mx-auto px-6 py-20">
          <div className="text-center mb-10">
            <h2 className="text-3xl md:text-4xl font-bold text-text-primary">
              Ready to Generate Your Highlight?
            </h2>
            <p className="text-text-secondary mt-3">
              Upload a full match video to get started.
            </p>
          </div>
          <UploadZone onUploadSuccess={handleUploadSuccess} />
        </section>
      </div>
    </PageWrapper>
  )
}
