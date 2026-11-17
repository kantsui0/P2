import { clientBadge } from '../utils/metrics'
import { decodeOrders } from '../services/details'
import { useCollection } from '../details/useCollection'
import { useSession } from '../session/session'
export function Badge({ id }: { id: string }) {
  const { token } = useSession()
  const data = useCollection(token!, id, 'pedidos', decodeOrders)
  return data.loading ? <p role="status">Carregando selo…</p> : data.error ? <><p role="alert">{data.error}</p><button onClick={data.refresh}>Recarregar selo</button></> : <span className="badge" aria-label="Selo do cliente">{clientBadge(data.items, Number(id))}</span>
}
