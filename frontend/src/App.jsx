import { BrowserRouter, Routes, Route } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { Toaster } from "react-hot-toast"
import Navbar from "./components/layout/Navbar"
import HomePage from "./pages/HomePage"
import MatchesPage from "./pages/MatchesPage"
import AboutPage from "./pages/AboutPage"
import ErrorBoundary from "./components/ErrorBoundary"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 0 },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ErrorBoundary>
          <Navbar />
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/matches" element={<MatchesPage />} />
            <Route path="/about" element={<AboutPage />} />
          </Routes>
        </ErrorBoundary>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: "#0F1626",
              color: "#F9FAFB",
              border: "1px solid #1F2937",
              borderRadius: "12px",
              fontSize: "14px",
            },
            success: { iconTheme: { primary: "#10B981", secondary: "#0F1626" } },
            error:   { iconTheme: { primary: "#EF4444", secondary: "#0F1626" } },
          }}
        />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
