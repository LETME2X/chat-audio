import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import type { Message } from '@/lib/supabase'
import { RealtimeChannel } from '@supabase/supabase-js'

export function useSupabase(userId?: string | null, tempUserId?: string | null) {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(true)
  const [channel, setChannel] = useState<RealtimeChannel | null>(null)

  useEffect(() => {
    // Fetch initial messages
    const fetchMessages = async () => {
      setLoading(true)
      const { data } = await supabase
        .from('messages')
        .select('*')
        .or(`user_id.eq.${userId},temp_user_id.eq.${tempUserId}`)
        .order('created_at', { ascending: true })
      
      if (data) setMessages(data as Message[])
      setLoading(false)
    }

    // Subscribe to new messages
    const channel = supabase
      .channel('messages')
      .on('postgres_changes', 
        { 
          event: 'INSERT', 
          schema: 'public', 
          table: 'messages',
          filter: `user_id=eq.${userId} OR temp_user_id=eq.${tempUserId}`
        },
        (payload) => {
          const newMessage = payload.new as Message
          setMessages(prev => [...prev, newMessage])
        }
      )
      .subscribe()

    setChannel(channel)
    fetchMessages()

    // Cleanup subscription
    return () => {
      channel.unsubscribe()
    }
  }, [userId, tempUserId])

  return { messages, loading }
}