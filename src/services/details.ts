import { api, ApiError } from './api'
import type { Item, OrderStatus } from '../utils/orders'
export type Order = { id: number; clienteId: number; data: string; status: OrderStatus; itens: Item[] }
export const channels = { telefone: 'Telefone', email: 'E-mail', whatsapp: 'WhatsApp', presencial: 'Presencial' } as const
export type Channel = keyof typeof channels
export type ContactInput = { titulo: string; texto: string; canal: Channel }
export type Contact = ContactInput & { id: number; clienteId: number; data: string }
function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new ApiError(null, 'Resposta inválida do servidor.')
  return value as Record<string, unknown>
}
export function decodeOrders(value: unknown): Order[] {
  const data = object(value)
  if (!Array.isArray(data.pedidos)) throw new ApiError(null, 'Resposta de pedidos inválida.')
  return data.pedidos.map(raw => {
    const order = object(raw)
    if (typeof order.id !== 'number' || typeof order.clienteId !== 'number' || typeof order.data !== 'string' || !['aberto', 'pago', 'cancelado'].includes(String(order.status)) || !Array.isArray(order.itens)) throw new ApiError(null, 'Pedido inválido na resposta.')
    const itens = order.itens.map(rawItem => {
      const item = object(rawItem)
      if (typeof item.titulo !== 'string' || typeof item.preco !== 'number' || !Number.isFinite(item.preco) || item.preco < 0 || !Number.isInteger(item.quantidade) || Number(item.quantidade) < 1) throw new ApiError(null, 'Item inválido na resposta.')
      return { titulo: item.titulo, preco: item.preco, quantidade: Number(item.quantidade) }
    })
    return { id: order.id, clienteId: order.clienteId, data: order.data, status: order.status as OrderStatus, itens }
  })
}
export function decodeContacts(value: unknown): Contact[] {
  const data = object(value)
  if (!Array.isArray(data.atendimentos)) throw new ApiError(null, 'Resposta de atendimentos inválida.')
  return data.atendimentos.map(raw => {
    const item = object(raw)
    if (typeof item.id !== 'number' || typeof item.clienteId !== 'number' || typeof item.data !== 'string' || typeof item.titulo !== 'string' || typeof item.texto !== 'string' || !Object.hasOwn(channels, String(item.canal))) throw new ApiError(null, 'Atendimento inválido na resposta.')
    return item as Contact
  }).sort((a, b) => b.data.localeCompare(a.data) || b.id - a.id)
}
export const detailApi = {
  createOrder: (token: string, id: string, itens: Item[]) => api.protected(`/clientes/${encodeURIComponent(id)}/pedidos`, token, { method: 'POST', body: { itens } }),
  editOrder: (token: string, id: number, itens: Item[]) => api.protected(`/pedidos/${id}`, token, { method: 'PATCH', body: { itens } }),
  status: (token: string, id: number, status: OrderStatus) => api.protected(`/pedidos/${id}`, token, { method: 'PATCH', body: { status } }),
  removeOrder: (token: string, id: number) => api.protected(`/pedidos/${id}`, token, { method: 'DELETE' }),
  saveContact: (token: string, clientId: string, input: ContactInput, id?: number) => api.protected(id === undefined ? `/clientes/${encodeURIComponent(clientId)}/atendimentos` : `/atendimentos/${id}`, token, { method: id === undefined ? 'POST' : 'PATCH', body: input }),
  removeContact: (token: string, id: number) => api.protected(`/atendimentos/${id}`, token, { method: 'DELETE' }),
}
