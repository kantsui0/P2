import { orderTotal, type OrderStatus } from './orders.ts'
import type { Order } from '../services/details'
export type NamedClient = { id: number; nome: string }
export function clientTotal(orders: readonly Order[], clientId: number): number {
  return orders.filter(order => order.clienteId === clientId && order.status !== 'cancelado').reduce((sum, order) => sum + orderTotal(order.itens), 0)
}
export function clientBadge(orders: readonly Order[], clientId: number): 'VIP' | 'Regular' | 'Sem compras' {
  const valid = orders.filter(order => order.clienteId === clientId && order.status !== 'cancelado')
  return valid.length === 0 ? 'Sem compras' : clientTotal(valid, clientId) >= 2000 ? 'VIP' : 'Regular'
}
export function topClients(clients: readonly NamedClient[], orders: readonly Order[]) {
  return clients.map(client => ({ ...client, total: clientTotal(orders, client.id) }))
    .sort((a, b) => b.total - a.total || a.id - b.id).slice(0, 3)
}
export function dashboardMetrics(orders: readonly Order[]) {
  const valid = orders.filter(order => order.status !== 'cancelado')
  const total = valid.reduce((sum, order) => sum + orderTotal(order.itens), 0)
  const statuses: OrderStatus[] = ['aberto', 'pago', 'cancelado']
  return { total, average: valid.length ? total / valid.length : 0,
    statuses: statuses.map(status => {
      const group = orders.filter(order => order.status === status)
      return { status, count: group.length, total: group.reduce((sum, order) => sum + orderTotal(order.itens), 0) }
    }) }
}
export type OrderSort = 'date-desc' | 'date-asc' | 'total-desc' | 'total-asc'
export function filterOrders(orders: readonly Order[], status: OrderStatus | '', min: number | null, max: number | null, sort: OrderSort) {
  return orders.filter(order => (!status || order.status === status) && (min === null || orderTotal(order.itens) >= min) && (max === null || orderTotal(order.itens) <= max))
    .sort((a, b) => {
      const comparison = sort.startsWith('date') ? a.data.localeCompare(b.data) : orderTotal(a.itens) - orderTotal(b.itens)
      return (sort.endsWith('desc') ? -comparison : comparison) || a.id - b.id
    })
}
