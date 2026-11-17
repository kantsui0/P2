import { Link } from 'react-router-dom'
import { dashboardMetrics, topClients } from '../utils/metrics'
import { money } from '../utils/orders'
import { useReports } from './useReports'
export function Dashboard() {
  const data = useReports()
  const metrics = dashboardMetrics(data.orders)
  const top = topClients(data.clients, data.orders)
  return <main><h1>Painel</h1><Link to="/clientes/novo">Novo cliente</Link>
    {data.loading ? <p role="status">Carregando painel…</p> : data.error ? <><p role="alert">{data.error}</p><button onClick={data.retry}>Tentar novamente</button></> : <>
      <div className="metrics"><section aria-label="Total de clientes"><h2>Total de clientes</h2><p>{data.clients.length}</p></section><section aria-label="Total vendido"><h2>Total vendido</h2><p>{money(metrics.total)}</p></section><section aria-label="Ticket médio"><h2>Ticket médio</h2><p>{money(metrics.average)}</p></section></div>
      <p>Total vendido e ticket médio consideram pedidos abertos e pagos.</p>
      <section aria-label="Pedidos por status"><h2>Pedidos por status</h2><div className="metrics">{metrics.statuses.map(group => <article key={group.status} aria-label={`Status ${group.status}`}><h3>{group.status}</h3><p>{group.count} pedidos</p><p>{money(group.total)}</p></article>)}</div></section>
      <section aria-label="Top 3 clientes"><h2>Top 3 clientes</h2>{top.length === 0 ? <p>Nenhum cliente cadastrado.</p> : <ol>{top.map(client => <li key={client.id}><Link to={`/clientes/${client.id}`}>{client.nome}</Link> — {money(client.total)}</li>)}</ol>}</section>
    </>}
  </main>
}
