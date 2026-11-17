import { useState, type SubmitEvent } from 'react'
import { useSession } from '../session/session'
import { decodeOrders, detailApi, type Order } from '../services/details'
import { errorMessage } from '../services/api'
import { allowedStatuses, displayDate, money, orderTotal, type Item, type OrderStatus } from '../utils/orders'
import { useCollection } from './useCollection'
import { Confirm } from './Confirm'

type DraftItem = { key: number; titulo: string; preco: string; quantidade: string }
function OrderForm({ order, save, cancel }: { order: Order | null; save: (items: Item[]) => Promise<void>; cancel: () => void }) {
  const [items, setItems] = useState<DraftItem[]>(() => order ? order.itens.map((item, key) => ({ key, titulo: item.titulo, preco: String(item.preco), quantidade: String(item.quantidade) })) : [{ key: 0, titulo: '', preco: '', quantidade: '1' }])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  function update(key: number, field: keyof Omit<DraftItem, 'key'>, value: string) { setItems(items.map(item => item.key === key ? { ...item, [field]: value } : item)) }
  async function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    if (busy) return
    if (!items.length) { setError('Adicione pelo menos um item.'); return }
    if (items.some(item => !item.titulo.trim())) { setError('Preencha o título de todos os itens.'); return }
    if (items.some(item => item.preco.trim() === '' || !Number.isFinite(Number(item.preco)) || Number(item.preco) < 0)) { setError('Informe um preço numérico maior ou igual a zero para todos os itens.'); return }
    if (items.some(item => item.quantidade.trim() === '' || !Number.isInteger(Number(item.quantidade)) || Number(item.quantidade) < 1)) { setError('A quantidade deve ser inteira e maior ou igual a 1.'); return }
    setBusy(true); setError('')
    try { await save(items.map(item => ({ titulo: item.titulo.trim(), preco: Number(item.preco), quantidade: Number(item.quantidade) }))) }
    catch (cause) { setError(errorMessage(cause)) }
    finally { setBusy(false) }
  }
  return <form onSubmit={submit} noValidate aria-label={order ? 'Editar itens' : 'Novo pedido'} aria-busy={busy}><h3>{order ? `Editar pedido #${order.id}` : 'Novo pedido'}</h3>
    {items.map((item, index) => <fieldset key={item.key} disabled={busy}><legend>Item {index + 1}</legend>
      <label htmlFor={`title-${item.key}`}>Título</label><input id={`title-${item.key}`} value={item.titulo} onChange={event => update(item.key, 'titulo', event.target.value)} />
      <label htmlFor={`price-${item.key}`}>Preço</label><input id={`price-${item.key}`} type="number" step="any" min="0" value={item.preco} onChange={event => update(item.key, 'preco', event.target.value)} />
      <label htmlFor={`qty-${item.key}`}>Quantidade</label><input id={`qty-${item.key}`} type="number" step="1" min="1" value={item.quantidade} onChange={event => update(item.key, 'quantidade', event.target.value)} />
      <button type="button" onClick={() => setItems(items.filter(current => current.key !== item.key))}>Remover item {index + 1}</button>
    </fieldset>)}
    {error && <p role="alert">{error}</p>}
    <button type="button" disabled={busy} onClick={() => setItems([...items, { key: Math.max(-1, ...items.map(item => item.key)) + 1, titulo: '', preco: '', quantidade: '1' }])}>Adicionar item</button>
    <button disabled={busy}>{busy ? 'Salvando…' : 'Salvar pedido'}</button><button type="button" disabled={busy} onClick={cancel}>Cancelar pedido</button>
  </form>
}
export function Orders({ clientId, onChanged }: { clientId: string; onChanged: () => void }) {
  const { token } = useSession()
  const collection = useCollection(token!, clientId, 'pedidos', decodeOrders)
  const [editing, setEditing] = useState<Order | null | undefined>(undefined)
  const [removing, setRemoving] = useState<Order | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function save(items: Item[]) {
    if (editing) {
      if (editing.status !== 'aberto') throw new Error('Somente pedidos abertos podem ser editados.')
      await detailApi.editOrder(token!, editing.id, items)
    } else await detailApi.createOrder(token!, clientId, items)
    setEditing(undefined); collection.refresh(); onChanged()
  }
  async function status(order: Order, next: OrderStatus) {
    if (busy || !allowedStatuses(order.status).includes(next)) return
    setBusy(true); setError('')
    try { await detailApi.status(token!, order.id, next); collection.refresh(); onChanged() }
    catch (cause) { setError(errorMessage(cause)) }
    finally { setBusy(false) }
  }
  async function remove() {
    if (!removing || busy) return
    setBusy(true); setError('')
    try { await detailApi.removeOrder(token!, removing.id); setRemoving(null); collection.refresh(); onChanged() }
    catch (cause) { setError(errorMessage(cause)) }
    finally { setBusy(false) }
  }
  return <section aria-labelledby="orders-title"><h2 id="orders-title">Pedidos</h2>
    {editing !== undefined ? <OrderForm order={editing} save={save} cancel={() => setEditing(undefined)} /> : <button disabled={busy || collection.loading} onClick={() => { setError(''); setEditing(null) }}>Novo pedido</button>}
    {error && !removing && <p role="alert">{error}</p>}
    {collection.loading ? <p role="status">Carregando pedidos…</p> : collection.error ? <><p role="alert">{collection.error}</p><button onClick={collection.refresh}>Tentar novamente</button></> : collection.items.length === 0 ? <p>Nenhum pedido.</p> : collection.items.map(order => <article className="record" key={order.id} aria-label={`Pedido ${order.id}`}><h3>Pedido #{order.id}</h3><p>Data: {displayDate(order.data)} · Status: {order.status}</p><ul>{order.itens.map((item, index) => <li key={index}>{item.titulo} — {item.quantidade} × {money(item.preco)}</li>)}</ul><p><strong>Total: {money(orderTotal(order.itens))}</strong></p>
      <div className="actions">{order.status === 'aberto' && <button disabled={busy || editing !== undefined} onClick={() => { setError(''); setEditing(order) }}>Editar itens</button>}
      {allowedStatuses(order.status).map(next => <button key={next} disabled={busy || editing !== undefined} onClick={() => status(order, next)}>{next === 'pago' ? 'Marcar como pago' : 'Cancelar pedido'}</button>)}
      <button disabled={busy || editing !== undefined} onClick={() => { setError(''); setRemoving(order) }}>Excluir pedido</button></div>
    </article>)}
    {removing && <Confirm title={`Excluir pedido #${removing.id}?`} busy={busy} error={error} cancel={() => setRemoving(null)} confirm={remove} />}
  </section>
}
