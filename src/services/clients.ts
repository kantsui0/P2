import { api, ApiError } from './api'
export type ClientInput = { nome: string; email: string; telefone: string; empresa: string; cidade: string }
export type Client = ClientInput & { id: number }
const invalid = () => new ApiError(null, 'A API retornou dados de clientes em formato inesperado.')
function record(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw invalid()
  return value as Record<string, unknown>
}
function client(value: unknown): Client {
  const data = record(value)
  if ((typeof data.id !== 'number' || !Number.isSafeInteger(data.id)) || typeof data.nome !== 'string' || typeof data.email !== 'string') throw invalid()
  const optional = (key: string) => {
    if (data[key] == null) return ''
    if (typeof data[key] !== 'string') throw invalid()
    return data[key]
  }
  return { id: data.id, nome: data.nome, email: data.email, telefone: optional('telefone'), empresa: optional('empresa'), cidade: optional('cidade') }
}
const path = (id: string) => `/clientes/${encodeURIComponent(id)}`
// Confirmed against servidor-crm/server.js: complete collections with total.
function count(value: unknown, collection: string): number {
  const data = record(value)
  if (Array.isArray(data[collection]) && Number.isSafeInteger(data.total) && Number(data.total) >= 0 && Number(data.total) === data[collection].length) return Number(data.total)
  throw new ApiError(null, 'Não foi possível confirmar as contagens. A exclusão está bloqueada.')
}
export const clientsApi = {
  async list(token: string, q: string, skip: number, signal?: AbortSignal) {
    const query = new URLSearchParams({ q, limit: '5', skip: String(skip) })
    const data = record(await api.protected(`/clientes?${query}`, token, { signal }))
    if (!Array.isArray(data.clientes) || !Number.isSafeInteger(data.total) || Number(data.total) < data.clientes.length) throw invalid()
    return { clientes: data.clientes.map(client), total: Number(data.total) }
  },
  async all(token: string, signal?: AbortSignal): Promise<Client[]> {
    const result: Client[] = []
    let skip = 0
    while (true) {
      const data = record(await api.protected(`/clientes?limit=100&skip=${skip}`, token, { signal }))
      if (!Array.isArray(data.clientes) || !Number.isSafeInteger(data.total) || Number(data.total) < 0) throw invalid()
      const page = data.clientes.map(client)
      result.push(...page)
      skip += page.length
      if (skip >= Number(data.total)) return result
      if (page.length === 0) throw invalid()
    }
  },
  async get(token: string, id: string, signal?: AbortSignal) {
    return client(await api.protected(path(id), token, { signal }))
  },
  async save(token: string, input: Partial<ClientInput>, id?: string) {
    await api.protected(id ? path(id) : '/clientes', token, { method: id ? 'PATCH' : 'POST', body: input })
  },
  async counts(token: string, id: string) {
    const [orders, contacts] = await Promise.all([
      api.protected(`${path(id)}/pedidos`, token),
      api.protected(`${path(id)}/atendimentos`, token),
    ])
    return { pedidos: count(orders, 'pedidos'), atendimentos: count(contacts, 'atendimentos') }
  },
  async remove(token: string, id: string) { await api.protected(path(id), token, { method: 'DELETE' }) },
}
