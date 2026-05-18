import { useQuery } from "@tanstack/react-query"
import { getJobStatus } from "../lib/api"

export const useJobPolling = (jobId) => {
  return useQuery({
    queryKey: ["job", jobId],
    queryFn: () => getJobStatus(jobId).then((r) => r.data),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === "done" || status === "failed") return false
      return 2000
    },
  })
}
