import { useEffect, useRef } from 'react'
export function Confirm({ title, busy, error, cancel, confirm }: { title: string; busy: boolean; error: string; cancel: () => void; confirm: () => void }) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => { ref.current?.showModal() }, [])
  return <dialog ref={ref} aria-label={title} onCancel={event => { event.preventDefault(); if (!busy) cancel() }}><h3>{title}</h3><p>Esta ação não pode ser desfeita.</p>{error && <p role="alert">{error}</p>}<div className="actions"><button autoFocus disabled={busy} onClick={cancel}>Cancelar</button><button disabled={busy} onClick={confirm}>{busy ? 'Excluindo…' : 'Confirmar exclusão'}</button></div></dialog>
}
