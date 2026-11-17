import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useSession } from '../session/session'
import { clientsApi } from '../services/clients'
import { ApiError, errorMessage } from '../services/api'
import { useClient } from './useClient'
import { Badge } from './Badge'
import { Orders } from '../details/Orders'
import { Contacts } from '../details/Contacts'
export function ClientDetail() {
  const { id = '' } = useParams()
  return <Detail key={id} id={id} />
}
function Detail({ id }: { id: string }) {
  const { token } = useSession()
  const [orderRevision, setOrderRevision] = useState(0)
  const resource = useClient(token!, id)
  const [counts, setCounts] = useState<{ pedidos: number; atendimentos: number } | null>(null)
  const [loading, setLoading] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState('')
  const dialog = useRef<HTMLDialogElement>(null)
  const navigate = useNavigate()
  useEffect(() => { if (counts) dialog.current?.showModal() }, [counts])
  async function prepareDelete() {
    setLoading(true); setError(''); setCounts(null)
    try { setCounts(await clientsApi.counts(token!, id)) }
    catch (cause) { setError(errorMessage(cause)) }
    finally { setLoading(false) }
  }
  async function remove() {
    if (!counts || deleting) return
    setDeleting(true); setError('')
    try {
      await clientsApi.remove(token!, id)
      navigate('/clientes', { replace: true })
    } catch (cause) {
      setError(cause instanceof ApiError && cause.status === 404 ? 'Cliente não encontrado' : errorMessage(cause))
    } finally { setDeleting(false) }
  }
  if (resource.loading) return <main><p role="status">Carregando cliente…</p></main>
  if (resource.error) return <main><p role="alert">{resource.error}</p><button onClick={resource.retry}>Tentar novamente</button> <Link to="/clientes">Voltar para clientes</Link></main>
  if (!resource.data) return null
  const client = resource.data
  return <main><Link to="/clientes">Voltar para clientes</Link><h1>{client.nome}</h1><Badge key={orderRevision} id={id} />
    <dl>{(['email', 'telefone', 'empresa', 'cidade'] as const).map(key => <div key={key}><dt>{{ email: 'E-mail', telefone: 'Telefone', empresa: 'Empresa', cidade: 'Cidade' }[key]}</dt><dd>{client[key] || 'Não informado'}</dd></div>)}</dl>
    <div className="actions"><Link to={`/clientes/${encodeURIComponent(id)}/editar`}>Editar</Link><button disabled={loading || deleting} onClick={prepareDelete}>{loading ? 'Conferindo vínculos…' : 'Excluir cliente'}</button></div>
    {loading && <p role="status">Carregando contagens de pedidos e atendimentos…</p>}
    {error && !counts && <p role="alert">{error}</p>}
    <Orders clientId={id} onChanged={() => setOrderRevision(value => value + 1)} />
    <Contacts clientId={id} />
    {counts && <dialog ref={dialog} aria-labelledby="delete-title" onCancel={event => { event.preventDefault(); if (!deleting) setCounts(null) }}>
      <h2 id="delete-title">Excluir {client.nome}?</h2>
      <p>Serão apagados este cliente, {counts.pedidos} pedidos e {counts.atendimentos} atendimentos.</p>
      <p>Esta ação não pode ser desfeita.</p>
      {error && <p role="alert">{error}</p>}
      <div className="actions"><button autoFocus disabled={deleting} onClick={() => { setCounts(null); setError('') }}>Cancelar</button><button disabled={deleting} onClick={remove}>{deleting ? 'Excluindo…' : 'Confirmar exclusão'}</button></div>
    </dialog>}
  </main>
}
