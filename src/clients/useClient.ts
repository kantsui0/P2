import { useEffect, useState } from 'react'
import { ApiError, errorMessage } from '../services/api'
import { clientsApi, type Client } from '../services/clients'
export function useClient(token: string, id: string | undefined) {
  const [data, setData] = useState<Client | null>(null)
  const [loading, setLoading] = useState(Boolean(id))
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    let active = true
    const controller = new AbortController()
    async function load() {
      setLoading(true); setError(''); setData(null)
      try {
        if (id) {
          const result = await clientsApi.get(token, id, controller.signal)
          if (active) setData(result)
        }
      } catch (cause) {
        if (active) setError(cause instanceof ApiError && cause.status === 404 ? 'Cliente não encontrado' : errorMessage(cause))
      } finally { if (active) setLoading(false) }
    }
    void load()
    return () => { active = false; controller.abort() }
  }, [token, id, attempt])
  return { data, loading, error, retry: () => setAttempt(value => value + 1) }
}
