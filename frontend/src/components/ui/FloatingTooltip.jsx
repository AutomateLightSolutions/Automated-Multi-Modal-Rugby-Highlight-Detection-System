import { createPortal } from "react-dom"

/**
 * Shared floating tooltip: position:fixed so it never pushes page content
 * around, anchored above the hovered element by default (20px gap), only
 * flipping below when there's genuinely no room above the viewport.
 *
 * Rendered via a portal straight into document.body — this page wraps
 * almost everything in Framer Motion's motion.div, which applies inline
 * `transform` styles for its animations. Any ancestor with a `transform`
 * becomes the containing block for descendant `position: fixed` elements
 * (a CSS quirk), so without the portal this tooltip would render relative
 * to whichever animated ancestor happens to have a transform applied,
 * landing far from the actual cursor instead of the true viewport.
 */
const GAP_PX = 20
const MIN_SPACE_ABOVE = GAP_PX + 90 // rough tooltip height + gap

export function computeTooltipAnchor(rect) {
  const flip = rect.top < MIN_SPACE_ABOVE
  return {
    x: rect.left + rect.width / 2,
    y: flip ? rect.bottom + GAP_PX : rect.top - GAP_PX,
    flip,
  }
}

export default function FloatingTooltip({ anchor, children }) {
  if (!anchor) return null
  return createPortal(
    <div
      className="fixed z-50 rounded-xl border border-border backdrop-blur-sm shadow-xl p-3 text-xs space-y-1 max-w-[220px] pointer-events-none"
      style={{
        left: anchor.x,
        top: anchor.y,
        transform: anchor.flip ? "translate(-50%, 0)" : "translate(-50%, -100%)",
        backgroundColor: "rgba(15, 22, 38, 0.6)",
      }}
    >
      {children}
    </div>,
    document.body,
  )
}
