import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useSession } from '../session/session'
import { clientsApi, type Client } from '../services/clients'
import { clientBadge } from '../utils/metrics'
import { decodeOrders, type Order } from '../services/details'
import { api, errorMessage } from '../services/api'
export function ClientList() {
  const { token } = useSession()
  const [query, setQuery] = useState({ q: '', skip: 0 })
  const [data, setData] = useState<{ clientes: Client[]; total: number }>({ clientes: [], total: 0 })
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const revision = useRef(0)
  useEffect(() => {
    let active = true
    const version = ++revision.current
    const controller = new AbortController()
    async function load() {
      setLoading(true); setError('')
      try {
        const [result, rawOrders] = await Promise.all([clientsApi.list(token!, query.q, query.skip, controller.signal), api.protected('/pedidos', token!, { signal: controller.signal })])
        const allOrders = decodeOrders(rawOrders)
        if (active && version === revision.current) {
          if (query.skip > 0 && query.skip >= result.total) setQuery(value => ({ ...value, skip: 0 }))
          else { setData(result); setOrders(allOrders) }
        }
      } catch (cause) {
        if (active && version === revision.current) setError(errorMessage(cause))
      } finally { if (active && version === revision.current) setLoading(false) }
    }
    void load()
    return () => { active = false; controller.abort() }
  }, [token, query, attempt])
  function change(q: string, skip: number) {
    revision.current++ // invalidate immediately, before effect cleanup
    setLoading(true); setError(''); setQuery({ q, skip })
  }
  return <main><h1>Clientes</h1><Link to="/clientes/novo">Novo cliente</Link>
    <label htmlFor="search">Buscar por nome ou e-mail</label>
    <input id="search" type="search" value={query.q} onChange={event => change(event.target.value, 0)} />
    {loading ? <p role="status">Carregando clientes…</p> : error ? <><p role="alert">{error}</p><button onClick={() => setAttempt(value => value + 1)}>Tentar novamente</button></> : <>
      <p>{data.total} clientes encontrados</p>
      {data.clientes.length === 0 ? <p>Nenhum cliente encontrado.</p> : <ul className="client-list">{data.clientes.map(client => <li key={client.id}><Link to={`/clientes/${encodeURIComponent(client.id)}`}>{client.nome}</Link><span>{client.email}</span><span className="badge" aria-label="Selo do cliente">{clientBadge(orders, client.id)}</span></li>)}</ul>}
      <nav aria-label="Paginação"><button disabled={query.skip === 0} onClick={() => change(query.q, query.skip - 5)}>Anterior</button><span>Página {Math.floor(query.skip / 5) + 1} de {Math.max(1, Math.ceil(data.total / 5))}</span><button disabled={query.skip + 5 >= data.total} onClick={() => change(query.q, query.skip + 5)}>Próxima</button></nav>
    </>}
  </main>
}
