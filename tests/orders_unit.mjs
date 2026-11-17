import assert from 'node:assert/strict'
import { orderTotal, allowedStatuses } from '../src/utils/orders.ts'
const items = Object.freeze([
  Object.freeze({ titulo: 'A', preco: 12.5, quantidade: 2 }),
  Object.freeze({ titulo: 'B', preco: 0, quantidade: 3 }),
  Object.freeze({ titulo: 'C', preco: 5, quantidade: 4 }),
])
assert.equal(orderTotal(items), 45)
assert.equal(orderTotal([]), 0)
assert.deepEqual(items.map(item => item.preco), [12.5, 0, 5])
assert.deepEqual(allowedStatuses('aberto'), ['pago', 'cancelado'])
assert.deepEqual(allowedStatuses('pago'), ['cancelado'])
assert.deepEqual(allowedStatuses('cancelado'), [])
console.log('PASS: total puro, entrada congelada, zero, lista vazia e três transições permitidas.')
