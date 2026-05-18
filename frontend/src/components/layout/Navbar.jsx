import { useState } from "react"
import { NavLink } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import { GitFork, BookOpen, Menu, X } from "lucide-react"

const LINKS = [
  { to: "/", label: "Home" },
  { to: "/matches", label: "Matches" },
  { to: "/about", label: "About" },
]

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <motion.header
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="fixed top-0 inset-x-0 z-50 bg-bg-primary/80 backdrop-blur-xl border-b border-border"
    >
      <nav className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <NavLink to="/" className="flex flex-col leading-tight">
          <span className="text-lg font-extrabold bg-hero-gradient bg-clip-text text-transparent">
            🏉 HighlightAI
          </span>
          <span className="text-[10px] text-text-muted tracking-wider">
            Rugby Highlight Generator
          </span>
        </NavLink>

        <div className="hidden md:flex items-center gap-1 relative">
          {LINKS.map(({ to, label }) => (
            <NavLink key={to} to={to} end={to === "/"}>
              {({ isActive }) => (
                <span className="relative px-4 py-2 text-sm font-medium transition-colors duration-200 rounded-lg block
                  hover:text-text-primary text-text-secondary"
                  style={{ color: isActive ? "#F9FAFB" : undefined }}
                >
                  {label}
                  {isActive && (
                    <motion.span
                      layoutId="nav-indicator"
                      className="absolute bottom-0 left-2 right-2 h-0.5 bg-accent-indigo rounded-full"
                    />
                  )}
                </span>
              )}
            </NavLink>
          ))}
        </div>

        <div className="hidden md:flex items-center gap-2">
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="btn-ghost p-2"
          >
            <GitFork size={18} />
          </a>
          <button className="btn-ghost flex items-center gap-1.5">
            <BookOpen size={16} />
            <span className="text-sm">Docs</span>
          </button>
        </div>

        <button
          className="md:hidden btn-ghost p-2"
          onClick={() => setMobileOpen((p) => !p)}
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </nav>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="md:hidden border-t border-border bg-bg-primary/95 overflow-hidden"
          >
            <div className="px-6 py-4 flex flex-col gap-1">
              {LINKS.map(({ to, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === "/"}
                  className={({ isActive }) =>
                    `px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-indigo-500/10 text-accent-indigo"
                        : "text-text-secondary hover:text-text-primary hover:bg-bg-tertiary"
                    }`
                  }
                  onClick={() => setMobileOpen(false)}
                >
                  {label}
                </NavLink>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  )
}
