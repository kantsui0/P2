import { useState, type SubmitEvent } from 'react'
import { BrowserRouter, Link, Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { SessionProvider } from './session/SessionContext'
import { useSession } from './session/session'
import { errorMessage } from './services/api'
import { ClientList } from './clients/ClientList'
import { ClientForm } from './clients/ClientForm'
import { ClientDetail } from './clients/ClientDetail'
import { Dashboard } from './reports/Dashboard'
import { AllOrders } from './reports/AllOrders'
import './App.css'

function destination(state: unknown): string {
  const from = state && typeof state === 'object' && 'from' in state ? state.from : null
  // Only internal destinations, never protocol-relative URLs or Login itself.
  return typeof from === 'string' && from.startsWith('/') && !from.startsWith('//') && !from.includes('\\') && from.split(/[?#]/)[0] !== '/login' ? from : '/painel'
}
function Login() {
  const session = useSession()
  const location = useLocation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  async function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    if (loading) return
    setLoading(true)
    setError('')
    try {
      await session.login(username.trim(), password)
    } catch (cause) {
      setError(errorMessage(cause))
    } finally {
      setLoading(false)
    }
  }
  if (session.token && session.user) return <Navigate to={destination(location.state)} replace />
  return <main className="login"><span className="tag">CRM DE CLIENTES</span><h1>Entrar</h1>
    <p>Acesse sua conta para continuar.</p>
    {session.notice && <p role="alert">{session.notice}</p>}
    <form onSubmit={submit} aria-busy={loading}>
      <label htmlFor="username">Usuário</label>
      <input id="username" autoComplete="username" value={username} onChange={event => setUsername(event.target.value)} required disabled={loading} />
      <label htmlFor="password">Senha</label>
      <input id="password" type="password" autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} required disabled={loading} />
      {error && <p role="alert">{error}</p>}
      <button disabled={loading} type="submit">{loading ? 'Entrando…' : 'Entrar'}</button>
    </form>
  </main>
}
function Protected() {
  const session = useSession()
  const location = useLocation()
  if (!session.token) return <Navigate to="/login" state={{ from: location.pathname + location.search + location.hash }} replace />
  if (session.loading) return <main><p role="status">Carregando sessão…</p></main>
  if (session.error) return <main><p role="alert">{session.error}</p><button onClick={session.retry}>Tentar novamente</button> <button onClick={session.logout}>Sair</button></main>
  return <><header><Link to="/painel" className="brand">CRM de clientes</Link><nav aria-label="Menu principal">
    <Link to="/painel">Painel</Link><Link to="/clientes">Clientes</Link><Link to="/pedidos">Pedidos</Link><Link to="/clientes/novo">Novo cliente</Link>
  </nav><span>{session.user?.name}</span><button onClick={session.logout}>Sair</button></header><Outlet /></>
}
function NotFound() {
  return <main><h1>Página não encontrada</h1><p>O endereço solicitado não existe.</p><Link to="/painel">Voltar para o Painel</Link></main>
}
export default function App() {
  return <BrowserRouter><SessionProvider><Routes>
    <Route path="/login" element={<Login />} />
    <Route element={<Protected />}>
      <Route index element={<Navigate to="/painel" replace />} />
      <Route path="/painel" element={<Dashboard />} />
      <Route path="/clientes" element={<ClientList />} />
      <Route path="/clientes/novo" element={<ClientForm key="new" />} />
      <Route path="/clientes/:id" element={<ClientDetail />} />
      <Route path="/clientes/:id/editar" element={<ClientForm />} />
      <Route path="/pedidos" element={<AllOrders />} />
      <Route path="*" element={<NotFound />} />
    </Route>
  </Routes></SessionProvider></BrowserRouter>
}
