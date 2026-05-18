import clsx from "clsx"

const SIZE_MAP = {
  sm: { outer: "w-6 h-6",  inner: "w-3 h-3",  border: "border-2" },
  md: { outer: "w-12 h-12", inner: "w-6 h-6",  border: "border-2" },
  lg: { outer: "w-20 h-20", inner: "w-10 h-10", border: "border-[3px]" },
}

export default function LoadingSpinner({ size = "md", text }) {
  const s = SIZE_MAP[size] ?? SIZE_MAP.md
  return (
    <div className="flex flex-col items-center gap-3">
      <div className={clsx("relative flex items-center justify-center", s.outer)}>
        <div
          className={clsx(
            "absolute inset-0 rounded-full border-accent-indigo border-t-transparent animate-spin",
            s.border
          )}
        />
        <div
          className={clsx(
            "rounded-full border-accent-cyan border-b-transparent",
            s.inner, s.border,
            "animate-spin [animation-direction:reverse]"
          )}
        />
      </div>
      {text && <p className="text-sm text-text-secondary">{text}</p>}
    </div>
  )
}
