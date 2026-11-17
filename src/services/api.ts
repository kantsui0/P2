export class ApiError extends Error {
  status: number | null
  constructor(status: number | null, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export const messages: Record<number, string> = {
  400: 'Dados inválidos. Confira os campos e tente novamente.',
  401: 'Sua sessão expirou. Entre novamente.',
  404: 'Recurso não encontrado.',
  409: 'Já existe um cliente com este e-mail.',
  500: 'O servidor apresentou um erro. Tente novamente.',
}
export function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : 'Não foi possível concluir a operação. Tente novamente.'
}

type Options = Omit<RequestInit, 'body'> & { body?: unknown; token?: string }
type ExpiryListener = (token: string) => void
const listeners = new Set<ExpiryListener>()
export function onSessionExpired(listener: ExpiryListener) {
  listeners.add(listener)
  return () => { listeners.delete(listener) }
}

// Protected calls require an explicit token; login is the only public API operation.
async function request(path: string, { body, token, ...options }: Options = {}): Promise<unknown> {
  const base = import.meta.env.VITE_API_URL?.replace(/\/$/, '')
  if (!base) throw new ApiError(null, 'Endereço da API não configurado.')
  const headers = new Headers(options.headers)
  if (body !== undefined) headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  let response: Response
  try {
    response = await fetch(`${base}${path}`, { ...options, headers, body: body === undefined ? undefined : JSON.stringify(body) })
  } catch {
    throw new ApiError(null, 'Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente.')
  }
  if (!response.ok) {
    if (response.status === 401 && token) listeners.forEach(listener => listener(token))
    const message = (response.status === 400 || response.status === 401) && path === '/auth/login'
      ? 'Usuário ou senha incorretos.'
      : messages[response.status] ?? 'Não foi possível concluir a operação. Tente novamente.'
    throw new ApiError(response.status, message)
  }
  if (response.status === 204) return null
  try {
    const text = await response.text()
    return text ? JSON.parse(text) as unknown : null
  } catch {
    throw new ApiError(response.status, 'O servidor retornou uma resposta inválida.')
  }
}

export const api = {
  async login(username: string, password: string): Promise<string> {
    const data = await request('/auth/login', { method: 'POST', body: { username, password } })
    if (!data || typeof data !== 'object' || !('accessToken' in data) || typeof data.accessToken !== 'string' || !data.accessToken) {
      throw new ApiError(null, 'O servidor não retornou um token de acesso válido.')
    }
    return data.accessToken
  },
  protected(path: string, token: string, options: Omit<Options, 'token'> = {}) {
    if (!token) return Promise.reject(new ApiError(401, messages[401]))
    return request(path, { ...options, token })
  },
  async me(token: string): Promise<{ name: string }> {
    const data = await this.protected('/auth/me', token)
    if (!data || typeof data !== 'object') throw new ApiError(null, 'Resposta de usuário inválida.')
    const user = data as Record<string, unknown>
    const name = user.nome
    if (typeof name !== 'string' || !name.trim()) throw new ApiError(null, 'A API não retornou o nome do usuário.')
    return { name }
  },
}
