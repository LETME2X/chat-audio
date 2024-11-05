'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/lib/context/AuthContext'
import { useTemporaryUser } from '@/lib/hooks/useTemporaryUser'
import LoginModal from '@/components/LoginModal'
import MessageList from '@/components/MessageList'
import AudioRecorder from '@/components/AudioRecorder'
import { Message } from '@/lib/supabase'

export default function Home() {
  const [socket, setSocket] = useState<WebSocket | null>(null)
  const [messageCount, setMessageCount] = useState(0)
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  
  const { user, signOut } = useAuth()
  const tempUserId = useTemporaryUser()

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws')
    
    ws.onopen = () => {
      console.log('Connected to WebSocket')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        if (data.type === 'transcription') {
          setMessages(prevMessages => {
            const updatedMessages = [...prevMessages]
            const lastMessage = updatedMessages[updatedMessages.length - 1]
            if (lastMessage && !lastMessage.is_ai) {
              lastMessage.transcription = data.text
              lastMessage.status = 'completed'
            }
            return updatedMessages
          })

          const analysisMessage: Message = {
            id: (Date.now() + 1).toString(),
            message: '',
            transcription: null,
            analysis: data.analysis,
            reply: null,
            is_ai: true,
            created_at: new Date().toISOString(),
            user_id: user?.id || null,
            temp_user_id: !user ? tempUserId : null,
            session_type: user ? 'logged-in' : 'temporary',
            status: 'completed'
          }
          
          setMessages(prevMessages => [...prevMessages, analysisMessage])
        }
        else if (data.type === 'ai_reply') {
          const replyMessage: Message = {
            id: (Date.now() + 2).toString(),
            message: '',
            transcription: null,
            analysis: null,
            reply: data.text,
            is_ai: true,
            created_at: new Date().toISOString(),
            user_id: user?.id || null,
            temp_user_id: !user ? tempUserId : null,
            session_type: user ? 'logged-in' : 'temporary',
            status: 'completed',
            processing_time: undefined
          }
          
          setMessages(prevMessages => [...prevMessages, replyMessage])
        }
      } catch (error) {
        console.error('Error parsing message:', error)
      }
    }

    setSocket(ws)

    return () => {
      ws.close()
    }
  }, [user, tempUserId])

  const handleAudioSend = async (audioBlob: Blob, duration: number) => {
    if (socket) {
      try {
        const reader = new FileReader()
        reader.readAsDataURL(audioBlob)
        reader.onloadend = () => {
          const base64Audio = reader.result as string
          const messageData = {
            type: 'audio',
            audio: base64Audio,
            tempUserId: user ? null : tempUserId,
            userId: user?.id,
            duration: duration
          }
          
          setMessages(prevMessages => [...prevMessages, {
            id: Date.now().toString(),
            message: '[Recording] Audio message',
            audio_url: URL.createObjectURL(audioBlob),
            audio_data: base64Audio,
            transcription: null,
            analysis: null,
            reply: null,
            is_ai: false,
            created_at: new Date().toISOString(),
            user_id: user?.id || null,
            temp_user_id: !user ? tempUserId : null,
            session_type: user ? 'logged-in' : 'temporary',
            status: 'processing' as const,
            audio_duration: duration,
            audio_format: 'wav',
            processing_time: 0
          } as Message])
          
          socket.send(JSON.stringify(messageData))
          
          if (!user) {
            const newCount = messageCount + 1
            setMessageCount(newCount)
            
            if (newCount >= 5) {
              setShowLoginModal(true)
            }
          }
        }
      } catch (error) {
        console.error('Error sending audio:', error)
      }
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center p-3 sm:p-6 bg-gray-50">
      <div className="z-10 w-full max-w-3xl">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-xl sm:text-2xl font-bold text-gray-800">Audio Chat App</h1>
          {user ? (
            <div className="flex items-center gap-4">
              <span className="text-gray-700 hidden sm:inline">{user.email}</span>
              <button
                onClick={signOut}
                className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowLoginModal(true)}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
            >
              Sign In
            </button>
          )}
        </div>
        
        {!user && (
          <div className="mb-4 text-sm text-gray-600">
            Messages remaining before login: {5 - messageCount}
          </div>
        )}

        <MessageList 
          userId={user?.id} 
          tempUserId={!user ? tempUserId : undefined}
          localMessages={messages}
        />
        
        <div className="flex justify-center mt-4">
          <AudioRecorder onSend={handleAudioSend} />
        </div>
      </div>

      <LoginModal 
        isOpen={showLoginModal} 
        onClose={() => setShowLoginModal(false)} 
      />
    </main>
  )
}