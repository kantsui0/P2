import { useState, type SubmitEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useSession } from '../session/session'
import { clientsApi, type ClientInput } from '../services/clients'
import { errorMessage } from '../services/api'
import { useClient } from './useClient'
const empty: ClientInput = { nome: '', email: '', telefone: '', empresa: '', cidade: '' }
export function ClientForm() {
  const { id } = useParams()
  const { token } = useSession()
  const resource = useClient(token!, id)
  if (resource.loading) return <main><p role="status">Carregando cliente…</p></main>
  if (resource.error) return <main><p role="alert">{resource.error}</p><button onClick={resource.retry}>Tentar novamente</button> <Link to="/clientes">Voltar para clientes</Link></main>
  const initial: ClientInput = resource.data ? { nome: resource.data.nome, email: resource.data.email, telefone: resource.data.telefone, empresa: resource.data.empresa, cidade: resource.data.cidade } : empty
  return <Form key={id ?? 'new'} id={id} token={token!} initial={initial} />
}
function Form({ id, token, initial }: { id?: string; token: string; initial: ClientInput }) {
  const [fields, setFields] = useState<ClientInput>(initial)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  async function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    if (saving) return
    const input = Object.fromEntries(Object.entries(fields).map(([key, value]) => [key, value.trim()])) as ClientInput
    if (!input.nome) { setError('Informe o nome do cliente.'); return }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.email)) { setError('Informe um e-mail válido.'); return }
    setSaving(true); setError('')
    try {
      const payload = id ? Object.fromEntries(Object.entries(input).filter(([key, value]) => value !== initial[key as keyof ClientInput])) : input
      await clientsApi.save(token, payload, id)
      navigate(id ? `/clientes/${encodeURIComponent(id)}` : '/clientes', { replace: true })
    } catch (cause) { setError(errorMessage(cause)) }
    finally { setSaving(false) }
  }
  return <main><h1>{id ? 'Editar cliente' : 'Novo cliente'}</h1><form noValidate onSubmit={submit} aria-busy={saving}>
    {(['nome', 'email', 'telefone', 'empresa', 'cidade'] as const).map(key => <div key={key}><label htmlFor={key}>{{ nome: 'Nome', email: 'E-mail', telefone: 'Telefone', empresa: 'Empresa', cidade: 'Cidade' }[key]}{key === 'nome' || key === 'email' ? ' (obrigatório)' : ''}</label><input id={key} type={key === 'email' ? 'email' : key === 'telefone' ? 'tel' : 'text'} required={key === 'nome' || key === 'email'} value={fields[key]} disabled={saving} onChange={event => setFields(value => ({ ...value, [key]: event.target.value }))} /></div>)}
    {error && <p role="alert">{error}</p>}<button disabled={saving}>{saving ? 'Salvando…' : 'Salvar'}</button>
    {!saving && <Link to={id ? `/clientes/${encodeURIComponent(id)}` : '/clientes'}>Cancelar</Link>}
  </form></main>
}
