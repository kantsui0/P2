import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react'
import { api, errorMessage, messages, onSessionExpired } from '../services/api'

import { SessionContext, type User } from './session'
const key = 'crm.accessToken'

export function SessionProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => sessionStorage.getItem(key))
  const currentToken = useRef(token)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(Boolean(token))
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [attempt, setAttempt] = useState(0)
  const clear = useCallback(() => {
    sessionStorage.removeItem(key)
    currentToken.current = null
    setToken(null)
    setUser(null)
    setError('')
  }, [])
  useEffect(() => onSessionExpired(expired => {
    if (expired === currentToken.current) {
      clear()
      setNotice(messages[401])
    }
  }), [clear])
  useEffect(() => {
    let active = true
    async function restore() {
      setLoading(true)
      setError('')
      try {
        if (token) {
          const result = await api.me(token)
          if (active && currentToken.current === token) setUser(result)
        }
      } catch (cause) {
        if (active && currentToken.current === token) setError(errorMessage(cause))
      } finally {
        if (active) setLoading(false)
      }
    }
    void restore()
    return () => { active = false }
  }, [token, attempt])

  async function login(username: string, password: string) {
    // Form owns loading/error; commit session only after /auth/me succeeds.
    const nextToken = await api.login(username, password)
    const nextUser = await api.me(nextToken)
    sessionStorage.setItem(key, nextToken)
    currentToken.current = nextToken
    setUser(nextUser)
    setNotice('')
    setError('')
    setToken(nextToken)
  }
  function logout() { clear(); setNotice(''); }
  return <SessionContext.Provider value={{ token, user, loading, error, notice, login, logout, retry: () => setAttempt(value => value + 1) }}>{children}</SessionContext.Provider>
}
