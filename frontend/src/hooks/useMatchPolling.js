import { useQuery } from "@tanstack/react-query"
import { getMatchStatus } from "../lib/api"

export const useMatchPolling = (matchId) => {
  return useQuery({
    queryKey: ["match", matchId],
    queryFn: () => getMatchStatus(matchId).then((r) => r.data),
    enabled: !!matchId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === "done" || status === "failed") return false
      return 3000
    },
  })
}
