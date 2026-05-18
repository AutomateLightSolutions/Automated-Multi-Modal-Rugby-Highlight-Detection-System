export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
      {Icon && (
        <div className="p-5 rounded-2xl bg-indigo-500/10 shadow-glow-indigo text-accent-indigo">
          <Icon size={40} />
        </div>
      )}
      <div className="space-y-1">
        <h3 className="text-lg font-semibold text-text-primary">{title}</h3>
        {description && (
          <p className="text-sm text-text-secondary max-w-sm">{description}</p>
        )}
      </div>
      {action && (
        <button className="btn-primary mt-2" onClick={action.onClick}>
          {action.label}
        </button>
      )}
    </div>
  )
}
