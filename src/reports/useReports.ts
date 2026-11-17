import { useEffect, useState } from 'react'
import { api, errorMessage } from '../services/api'
import { clientsApi, type Client } from '../services/clients'
import { decodeOrders, type Order } from '../services/details'
import { useSession } from '../session/session'
export function useReports() {
  const { token } = useSession()
  const [data, setData] = useState<{ clients: Client[]; orders: Order[] }>({ clients: [], orders: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    let active = true
    const controller = new AbortController()
    async function load() {
      setLoading(true); setError('')
      try {
        const [clients, rawOrders] = await Promise.all([clientsApi.all(token!, controller.signal), api.protected('/pedidos', token!, { signal: controller.signal })])
        const orders = decodeOrders(rawOrders)
        if (active) setData({ clients, orders })
      } catch (cause) { if (active) setError(errorMessage(cause)) }
      finally { if (active) setLoading(false) }
    }
    void load()
    return () => { active = false; controller.abort() }
  }, [token, attempt])
  return { ...data, loading, error, retry: () => setAttempt(value => value + 1) }
}
