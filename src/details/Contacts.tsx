import { useState, type SubmitEvent } from 'react'
import { useSession } from '../session/session'
import { channels, decodeContacts, detailApi, type Channel, type Contact, type ContactInput } from '../services/details'
import { errorMessage } from '../services/api'
import { displayDate } from '../utils/orders'
import { useCollection } from './useCollection'
import { Confirm } from './Confirm'
function ContactForm({ contact, save, cancel }: { contact: Contact | null; save: (input: ContactInput) => Promise<void>; cancel: () => void }) {
  const [input, setInput] = useState<ContactInput>(() => contact ? { titulo: contact.titulo, texto: contact.texto, canal: contact.canal } : { titulo: '', texto: '', canal: 'telefone' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    if (busy) return
    if (!input.titulo.trim() || !input.texto.trim()) { setError('Preencha o título e o texto do atendimento.'); return }
    setBusy(true); setError('')
    try { await save({ titulo: input.titulo.trim(), texto: input.texto.trim(), canal: input.canal }) }
    catch (cause) { setError(errorMessage(cause)) }
    finally { setBusy(false) }
  }
  return <form aria-label={contact ? 'Editar atendimento' : 'Novo atendimento'} onSubmit={submit} noValidate aria-busy={busy}><h3>{contact ? 'Editar atendimento' : 'Novo atendimento'}</h3><fieldset disabled={busy}>
    <label htmlFor="contact-title">Título do atendimento</label><input id="contact-title" value={input.titulo} onChange={event => setInput({ ...input, titulo: event.target.value })} />
    <label htmlFor="contact-text">Texto</label><textarea id="contact-text" value={input.texto} onChange={event => setInput({ ...input, texto: event.target.value })} />
    <label htmlFor="contact-channel">Canal</label><select id="contact-channel" value={input.canal} onChange={event => setInput({ ...input, canal: event.target.value as Channel })}>{Object.entries(channels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
  </fieldset>{error && <p role="alert">{error}</p>}<button disabled={busy}>{busy ? 'Salvando…' : 'Salvar atendimento'}</button><button type="button" disabled={busy} onClick={cancel}>Cancelar atendimento</button></form>
}
export function Contacts({ clientId }: { clientId: string }) {
  const { token } = useSession()
  const collection = useCollection(token!, clientId, 'atendimentos', decodeContacts)
  const [filter, setFilter] = useState<Channel | ''>('')
  const [editing, setEditing] = useState<Contact | null | undefined>(undefined)
  const [removing, setRemoving] = useState<Contact | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const filtered = collection.items.filter(item => !filter || item.canal === filter)
  async function save(input: ContactInput) {
    await detailApi.saveContact(token!, clientId, input, editing?.id)
    setEditing(undefined); collection.refresh()
  }
  async function remove() {
    if (!removing || busy) return
    setBusy(true); setError('')
    try { await detailApi.removeContact(token!, removing.id); setRemoving(null); collection.refresh() }
    catch (cause) { setError(errorMessage(cause)) }
    finally { setBusy(false) }
  }
  return <section aria-labelledby="contacts-title"><h2 id="contacts-title">Histórico de atendimento</h2>
    <label htmlFor="channel-filter">Filtrar por canal</label><select id="channel-filter" value={filter} onChange={event => setFilter(event.target.value as Channel | '')}><option value="">Todos</option>{Object.entries(channels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
    {editing !== undefined ? <ContactForm contact={editing} save={save} cancel={() => setEditing(undefined)} /> : <button disabled={busy || collection.loading} onClick={() => { setError(''); setEditing(null) }}>Novo atendimento</button>}
    {error && !removing && <p role="alert">{error}</p>}
    {collection.loading ? <p role="status">Carregando atendimentos…</p> : collection.error ? <><p role="alert">{collection.error}</p><button onClick={collection.refresh}>Tentar novamente</button></> : <><p aria-live="polite">{filtered.length} atendimentos</p>{filtered.length === 0 ? <p>Nenhum atendimento para este filtro.</p> : filtered.map(contact => <article className="record" key={contact.id} aria-label={`Atendimento ${contact.id}`}><h3>{contact.titulo}</h3><p className="contact-text">{contact.texto}</p><p>{channels[contact.canal]} · {displayDate(contact.data)}</p><div className="actions"><button disabled={busy || editing !== undefined} onClick={() => { setError(''); setEditing(contact) }}>Editar atendimento</button><button disabled={busy || editing !== undefined} onClick={() => { setError(''); setRemoving(contact) }}>Excluir atendimento</button></div></article>)}</>}
    {removing && <Confirm title={`Excluir atendimento “${removing.titulo}”?`} busy={busy} error={error} cancel={() => setRemoving(null)} confirm={remove} />}
  </section>
}
