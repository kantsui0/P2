export type Item = { id?: number; titulo: string; preco: number; quantidade: number }
export type OrderStatus = 'aberto' | 'pago' | 'cancelado'
export function orderTotal(itens: readonly Item[]): number {
  return itens.reduce((total, item) => total + item.preco * item.quantidade, 0)
}
export function allowedStatuses(status: OrderStatus): OrderStatus[] {
  return status === 'aberto' ? ['pago', 'cancelado'] : status === 'pago' ? ['cancelado'] : []
}
export const money = (value: number) => value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
export function displayDate(value: string) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value)
  return match ? `${match[3]}/${match[2]}/${match[1]}` : value
}
