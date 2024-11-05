'use client'
import React, { useEffect, useRef } from 'react'
import { Message } from '@/lib/supabase'
import { useSupabase } from '../lib/hooks/useSupabase'
import MessageItem from './MessageItem'

interface MessageListProps {
  userId?: string | null
  tempUserId?: string | null
  localMessages: Message[]
}

export default function MessageList({ userId, tempUserId, localMessages }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { messages, loading } = useSupabase(userId, tempUserId)
  
  const allMessages = [...messages, ...localMessages].sort((a, b) => {
    const dateA = a.created_at ? new Date(a.created_at).getTime() : 0
    const dateB = b.created_at ? new Date(b.created_at).getTime() : 0
    return dateA - dateB
  })

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [allMessages])

  if (loading && messages.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="loading-spinner" />
      </div>
    )
  }

  return (
    <div className="message-container">
      {allMessages.map((message) => (
        <MessageItem key={message.id} message={message} />
      ))}
      <div ref={messagesEndRef} />
    </div>
  )
}