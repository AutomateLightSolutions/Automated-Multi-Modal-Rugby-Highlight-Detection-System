import { Component } from "react"
import { AlertTriangle } from "lucide-react"

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center px-6">
          <div className="glass-card p-10 max-w-md text-center space-y-4">
            <div className="p-4 rounded-2xl bg-red-500/10 text-accent-red w-fit mx-auto">
              <AlertTriangle size={36} />
            </div>
            <h2 className="text-xl font-bold text-text-primary">Something went wrong</h2>
            <p className="text-sm text-text-secondary">
              {this.state.error?.message ?? "An unexpected error occurred."}
            </p>
            <button className="btn-primary" onClick={() => window.location.reload()}>
              Reload Page
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
