import { useState } from 'react'
import { Link } from 'react-router-dom'
import { filterOrders, type OrderSort } from '../utils/metrics'
import { displayDate, money, orderTotal, type OrderStatus } from '../utils/orders'
import { useReports } from './useReports'
export function AllOrders() {
  const data = useReports()
  const [status, setStatus] = useState<OrderStatus | ''>('')
  const [min, setMin] = useState('')
  const [max, setMax] = useState('')
  const [sort, setSort] = useState<OrderSort>('date-desc')
  const minValue = min === '' ? null : Number(min)
  const maxValue = max === '' ? null : Number(max)
  const invalid = [minValue, maxValue].some(value => value !== null && (!Number.isFinite(value) || value < 0)) || (minValue !== null && maxValue !== null && minValue > maxValue)
  const orders = invalid ? [] : filterOrders(data.orders, status, minValue, maxValue, sort)
  const names = new Map(data.clients.map(client => [client.id, client.nome]))
  return <main><h1>Todos os pedidos</h1>
    <div className="filters"><div><label htmlFor="order-status">Status</label><select id="order-status" value={status} onChange={event => setStatus(event.target.value as OrderStatus | '')}><option value="">Todos</option><option value="aberto">Aberto</option><option value="pago">Pago</option><option value="cancelado">Cancelado</option></select></div>
      <div><label htmlFor="min-total">Valor mínimo</label><input id="min-total" type="number" min="0" step="any" value={min} onChange={event => setMin(event.target.value)} /></div>
      <div><label htmlFor="max-total">Valor máximo</label><input id="max-total" type="number" min="0" step="any" value={max} onChange={event => setMax(event.target.value)} /></div>
      <div><label htmlFor="order-sort">Ordenar por</label><select id="order-sort" value={sort} onChange={event => setSort(event.target.value as OrderSort)}><option value="date-desc">Data: mais recentes</option><option value="date-asc">Data: mais antigos</option><option value="total-desc">Total: maior primeiro</option><option value="total-asc">Total: menor primeiro</option></select></div></div>
    {invalid && <p role="alert">Informe uma faixa válida: valores não negativos e mínimo menor ou igual ao máximo.</p>}
    {data.loading ? <p role="status">Carregando pedidos…</p> : data.error ? <><p role="alert">{data.error}</p><button onClick={data.retry}>Tentar novamente</button></> : !invalid && <><p>{orders.length} pedidos encontrados</p>{orders.length === 0 ? <p>Nenhum pedido para estes filtros.</p> : orders.map(order => <article className="record" key={order.id} aria-label={`Pedido ${order.id}`}><h2><Link to={`/clientes/${order.clienteId}`}>{names.get(order.clienteId) ?? `Cliente #${order.clienteId}`}</Link></h2><p>Pedido #{order.id} · {displayDate(order.data)} · {order.status}</p><p>Total: {money(orderTotal(order.itens))}</p></article>)}</>}
  </main>
}
