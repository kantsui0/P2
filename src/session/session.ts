import { createContext, useContext } from 'react'
export type User = { name: string }
export type Session = {
  token: string | null; user: User | null; loading: boolean; error: string; notice: string
  login: (username: string, password: string) => Promise<void>
  logout: () => void; retry: () => void
}
export const SessionContext = createContext<Session | null>(null)
export function useSession() {
  const context = useContext(SessionContext)
  if (!context) throw new Error('SessionProvider ausente')
  return context
}
