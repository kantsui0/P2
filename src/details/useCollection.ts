import { useEffect, useState } from 'react'
import { api, errorMessage } from '../services/api'
export function useCollection<T>(token: string, id: string, kind: string, decode: (value: unknown) => T[]) {
  const [items, setItems] = useState<T[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [revision, setRevision] = useState(0)
  useEffect(() => {
    let active = true
    const controller = new AbortController()
    async function load() {
      setLoading(true); setError('')
      try {
        const data = decode(await api.protected(`/clientes/${encodeURIComponent(id)}/${kind}`, token, { signal: controller.signal }))
        if (active) setItems(data)
      } catch (cause) { if (active) setError(errorMessage(cause)) }
      finally { if (active) setLoading(false) }
    }
    void load()
    return () => { active = false; controller.abort() }
  }, [token, id, kind, decode, revision])
  return { items, loading, error, refresh: () => { setLoading(true); setRevision(value => value + 1) } }
}
