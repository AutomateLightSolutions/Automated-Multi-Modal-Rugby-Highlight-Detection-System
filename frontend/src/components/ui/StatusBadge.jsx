import {
  CloudUpload, Cpu, Zap, CheckCircle, XCircle, Clock, Loader2, Circle,
} from "lucide-react"

const STATUS_MAP = {
  uploaded:   { cls: "badge-cyan",    Icon: CloudUpload, label: "Uploaded" },
  extracting: { cls: "badge-amber",   Icon: Cpu,         label: "Extracting" },
  processing: { cls: "badge-indigo",  Icon: Zap,         label: "Processing" },
  done:       { cls: "badge-emerald", Icon: CheckCircle, label: "Complete" },
  failed:     { cls: "badge-red",     Icon: XCircle,     label: "Failed" },
  pending:    { cls: "badge-amber",   Icon: Clock,       label: "Pending" },
  running:    { cls: "badge-indigo",  Icon: Loader2,     label: "Running", spin: true },
}

export default function StatusBadge({ status }) {
  const cfg = STATUS_MAP[status] ?? {
    cls: "badge-cyan", Icon: Circle, label: status,
  }
  const { cls, Icon, label, spin } = cfg
  return (
    <span className={cls}>
      <Icon size={12} className={spin ? "animate-spin" : ""} />
      {label}
    </span>
  )
}
