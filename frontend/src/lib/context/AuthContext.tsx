'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { User, Session } from '@supabase/supabase-js'
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'

type AuthContextType = {
  user: User | null
  session: Session | null
  signInWithGoogle: () => Promise<void>
  signOut: () => Promise<void>
  isAnonymous: boolean
  remainingChats: number | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const supabase = createClientComponentClient()
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [remainingChats, setRemainingChats] = useState<number | null>(null)

  useEffect(() => {
    // Get initial chat count and session
    const initializeSession = async () => {
      const chatCount = parseInt(localStorage.getItem('chat_count') || '0')
      const { data: { session } } = await supabase.auth.getSession()
      
      setSession(session)
      setUser(session?.user ?? null)
      setRemainingChats(session ? null : Math.max(0, 5 - chatCount))
    }

    initializeSession()

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
      
      if (session?.user) {
        // Merge sessions on login
        const tempUserId = localStorage.getItem('temp_user_id')
        if (tempUserId) {
          await supabase.rpc('merge_user_sessions', {
            p_temp_user_id: tempUserId,
            p_user_id: session.user.id
          })
        }
        setRemainingChats(null) // Unlimited for logged-in users
      } else {
        // Reset on logout
        const newTempId = crypto.randomUUID()
        localStorage.setItem('temp_user_id', newTempId)
        localStorage.setItem('chat_count', '0')
        setRemainingChats(5)
      }
    })

    return () => subscription.unsubscribe()
  }, [supabase])

  const signInWithGoogle = async () => {
    const tempUserId = localStorage.getItem('temp_user_id')
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
        queryParams: {
          temp_user_id: tempUserId || ''
        }
      }
    })
  }

  const signOut = async () => {
    await supabase.auth.signOut()
  }

  return (
    <AuthContext.Provider value={{
      user,
      session,
      signInWithGoogle,
      signOut,
      isAnonymous: !user,
      remainingChats
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}