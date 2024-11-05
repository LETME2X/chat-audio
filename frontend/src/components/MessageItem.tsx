'use client'
import React from 'react'
import { Message } from '@/lib/supabase'

interface MessageItemProps {
  message: Message
}

export default function MessageItem({ message }: MessageItemProps) {
  const isUserMessage = !message.is_ai
  const isPending = message.status === 'pending' && !message.transcription

  const formatTime = (dateString: string | null | undefined) => {
    if (!dateString) return ''
    return new Date(dateString).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  return (
    <div className={`flex ${isUserMessage ? 'justify-end' : 'justify-start'} mb-2`}>
      <div 
        className={`max-w-[65%] w-fit rounded-lg shadow-sm p-3 message-bubble relative ${
          isUserMessage ? 'bg-blue-50 user-message' : 'bg-white ai-message'
        } ${isPending ? 'opacity-70' : ''}`}
      >
        {isPending && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/50 rounded-lg">
            <div className="loading-spinner" />
          </div>
        )}

        {/* User Message with Audio Icon */}
        {isUserMessage && message.audio_url && (
          <div className="flex items-center gap-1.5 mb-2">
            <svg viewBox="0 0 24 24" className="w-4 h-4 text-blue-500" fill="currentColor">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
            </svg>
            <span className="text-xs text-gray-600">Audio Message</span>
          </div>
        )}

        {/* Message Transcription */}
        {isUserMessage && message.transcription && (
          <div className="text-xs text-gray-800 font-medium mb-1.5">
            {message.transcription}
          </div>
        )}

        {/* AI Response */}
        {!isUserMessage && (
          <>
            {message.analysis && (
              <div className="mb-3">
                <div className="font-medium text-blue-600 text-xs mb-1">Communication Tip:</div>
                <div className="text-xs text-gray-700">{message.analysis}</div>
              </div>
            )}
            {message.reply && (
              <div>
                <div className="font-medium text-blue-600 text-xs mb-1">AI Response:</div>
                <div className="text-xs text-gray-700">{message.reply}</div>
              </div>
            )}
          </>
        )}

        {/* Timestamp */}
        <div className="flex justify-end text-[9px] text-gray-400 mt-2">
          {formatTime(message.created_at)}
        </div>
      </div>
    </div>
  )
}
