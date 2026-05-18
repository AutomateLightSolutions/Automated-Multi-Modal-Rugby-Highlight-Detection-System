import PropTypes from "prop-types";
import { motion } from "framer-motion";
import { ArrowRight, Eye, Mic, Activity, Zap } from "lucide-react";
import PageWrapper from "../components/layout/PageWrapper";

// ── Pipeline data ─────────────────────────────────────────────────────────────

const BEFORE_PARALLEL = [
  { label: "Upload", color: "border-accent-indigo  text-accent-indigo" },
  {
    label: "FFmpeg\nExtraction",
    color: "border-accent-cyan    text-accent-cyan",
  },
];

const PARALLEL_MODULES = [
  {
    label: "Visual\nModule",
    Icon: Eye,
    color: "border-accent-purple  text-accent-purple",
    bg: "bg-purple-500/10",
  },
  {
    label: "Commentary\nModule",
    Icon: Mic,
    color: "border-accent-indigo  text-accent-indigo",
    bg: "bg-indigo-500/10",
  },
  {
    label: "Audio\nModule",
    Icon: Activity,
    color: "border-accent-emerald text-accent-emerald",
    bg: "bg-emerald-500/10",
  },
];

const AFTER_PARALLEL = [
  { label: "Fusion\nEngine", color: "border-accent-amber   text-accent-amber" },
  { label: "NMS\nSelection", color: "border-accent-cyan    text-accent-cyan" },
  {
    label: "Video\nAssembly",
    color: "border-accent-emerald text-accent-emerald",
  },
];

// ── Team / Tech data ──────────────────────────────────────────────────────────

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
];

const TECH = [
  {
    name: "PyTorch",
    color: "text-orange-400 border-orange-400/30 bg-orange-400/5",
  },
  {
    name: "FastAPI",
    color: "text-emerald-400 border-emerald-400/30 bg-emerald-400/5",
  },
  {
    name: "Celery",
    color: "text-green-400  border-green-400/30  bg-green-400/5",
  },
  { name: "Redis", color: "text-red-400    border-red-400/30    bg-red-400/5" },
  {
    name: "PostgreSQL",
    color: "text-blue-400   border-blue-400/30   bg-blue-400/5",
  },
  {
    name: "FFmpeg",
    color: "text-yellow-400 border-yellow-400/30 bg-yellow-400/5",
  },
  {
    name: "Whisper",
    color: "text-purple-400 border-purple-400/30 bg-purple-400/5",
  },
  {
    name: "React",
    color: "text-cyan-400   border-cyan-400/30   bg-cyan-400/5",
  },
  {
    name: "Tailwind CSS",
    color: "text-sky-400    border-sky-400/30    bg-sky-400/5",
  },
];

// ── Sub-components ────────────────────────────────────────────────────────────

function PipelineBox({ label, color, delay = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay }}
      className={`border rounded-xl px-4 py-3 text-xs font-semibold whitespace-pre-line text-center
                  min-w-[90px] bg-bg-tertiary ${color}`}
    >
      {label}
    </motion.div>
  );
}
PipelineBox.propTypes = {
  label: PropTypes.string.isRequired,
  color: PropTypes.string.isRequired,
  delay: PropTypes.number,
};

function Arrow() {
  return <ArrowRight size={16} className="text-text-muted shrink-0" />;
}

// Fork connector: vertical bar + three horizontal stubs pointing right
function ForkConnector() {
  return (
    <div className="flex items-center self-stretch">
      <div className="relative w-5 self-stretch flex flex-col justify-between py-[18px]">
        <div className="absolute left-0 top-[18px] bottom-[18px] w-px bg-border-light" />
        <div className="h-px w-full bg-border-light" />
        <div className="h-px w-full bg-border-light" />
        <div className="h-px w-full bg-border-light" />
      </div>
    </div>
  );
}

// Join connector: three horizontal stubs pointing right + vertical bar
function JoinConnector() {
  return (
    <div className="flex items-center self-stretch">
      <div className="relative w-5 self-stretch flex flex-col justify-between py-[18px]">
        <div className="absolute right-0 top-[18px] bottom-[18px] w-px bg-border-light" />
        <div className="h-px w-full bg-border-light" />
        <div className="h-px w-full bg-border-light" />
        <div className="h-px w-full bg-border-light" />
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function AboutPage() {
  return (
    <PageWrapper>
      <div className="pt-16 max-w-6xl mx-auto px-6 py-16 space-y-24">
        {/* ── Architecture ── */}
        <section>
          <h2 className="text-3xl font-bold text-text-primary mb-2">
            System Architecture
          </h2>
          <p className="text-text-secondary mb-10">
            End-to-end pipeline from raw video to downloadable highlight reel.
          </p>

          <div className="glass-card p-8 overflow-x-auto">
            {/* Main pipeline row */}
            <div className="flex items-center gap-2 min-w-max">
              {/* Sequential: Upload → FFmpeg */}
              {BEFORE_PARALLEL.map((node, i) => (
                <div key={node.label} className="flex items-center gap-2">
                  <PipelineBox
                    label={node.label}
                    color={node.color}
                    delay={i * 0.1}
                  />
                  <Arrow />
                </div>
              ))}

              {/* Fork → Parallel modules → Join */}
              <div className="flex items-stretch gap-0">
                <ForkConnector />

                {/* Parallel block */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.96 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.2 }}
                  className="relative border-2 border-dashed border-indigo-500/40 rounded-2xl
                             bg-indigo-500/5 p-4 flex flex-col gap-2.5"
                >
                  {/* Floating label */}
                  <div className="absolute -top-6 left-1/2 -translate-x-1/2 px-2 bg-bg-card">
                    <span
                      className="flex items-center gap-1 text-[10px] font-bold
                                     tracking-widest uppercase text-accent-indigo whitespace-nowrap"
                    >
                      <Zap size={10} />
                      Concurrent · 3 Celery Workers
                    </span>
                  </div>

                  {/* Pulsing active indicator
                  <span className="absolute -top-1.5 -right-1.5 flex h-3 w-3">
                    <span
                      className="animate-ping absolute inline-flex h-full w-full
                                     rounded-full bg-accent-indigo opacity-60"
                    />
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-accent-indigo" />
                  </span> */}

                  {PARALLEL_MODULES.map((mod, i) => (
                    <motion.div
                      key={mod.label}
                      initial={{ opacity: 0, x: -8 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true }}
                      transition={{ delay: 0.25 + i * 0.08 }}
                      className={`flex items-center gap-2.5 border rounded-xl px-4 py-2.5
                                  text-xs font-semibold min-w-[150px] ${mod.color} ${mod.bg}`}
                    >
                      <mod.Icon size={14} className="shrink-0" />
                      <span className="whitespace-pre-line leading-tight">
                        {mod.label}
                      </span>
                    </motion.div>
                  ))}
                </motion.div>

                <JoinConnector />
              </div>

              <Arrow />

              {/* Sequential: Fusion → NMS → Assembly */}
              {AFTER_PARALLEL.map((node, i) => (
                <div key={node.label} className="flex items-center gap-2">
                  <PipelineBox
                    label={node.label}
                    color={node.color}
                    delay={0.5 + i * 0.1}
                  />
                  {i < AFTER_PARALLEL.length - 1 && <Arrow />}
                </div>
              ))}
            </div>

            {/* Legend */}
            <div className="mt-6 flex items-center gap-3 flex-wrap">
              <span className="badge bg-indigo-500/10 text-accent-indigo border border-indigo-500/20">
                Celery Workers (concurrency=3)
              </span>
              <span className="badge bg-cyan-500/10 text-accent-cyan border border-cyan-500/20">
                Redis Message Broker
              </span>
              <span className="badge bg-amber-500/10 text-accent-amber border border-amber-500/20">
                PostgreSQL State Store
              </span>
              <span className="badge bg-purple-500/10 text-accent-purple border border-purple-500/20">
                ⚡ Modules run in parallel
              </span>
            </div>
          </div>
        </section>

        {/* ── Team ── */}
        <section>
          <h2 className="text-3xl font-bold text-text-primary mb-2">
            The Team
          </h2>
          <p className="text-text-secondary mb-10">
            Final year research project — each member owns one AI module.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {TEAM.map((member, i) => (
              <motion.div
                key={member.name}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.12 }}
                className="glass-card-hover p-6 space-y-4"
              >
                <div
                  className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${member.gradient}
                                 flex items-center justify-center text-white text-xl font-extrabold`}
                >
                  {member.initials}
                </div>
                <div>
                  <h3 className="font-semibold text-text-primary">
                    {member.name}
                  </h3>
                  <p className="text-sm text-accent-indigo font-medium">
                    {member.role}
                  </p>
                  <p className="text-sm text-text-secondary mt-2">
                    {member.desc}
                  </p>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {member.stack.map((t) => (
                    <span
                      key={t}
                      className="badge bg-bg-tertiary text-text-muted
                                             border border-border text-[11px]"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </section>

        {/* ── Tech Stack ── */}
        <section>
          <h2 className="text-3xl font-bold text-text-primary mb-2">
            Technology Stack
          </h2>
          <p className="text-text-secondary mb-10">
            The tools powering every layer of the system.
          </p>
          <div className="flex flex-wrap gap-3">
            {TECH.map((t, i) => (
              <motion.div
                key={t.name}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.05 }}
                className={`glass-card px-5 py-3 font-semibold text-sm border ${t.color}
                            hover:-translate-y-0.5 transition-transform cursor-default`}
              >
                {t.name}
              </motion.div>
            ))}
          </div>
        </section>
      </div>
    </PageWrapper>
  );
}
