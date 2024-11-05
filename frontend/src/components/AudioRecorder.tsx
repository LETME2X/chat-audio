'use client'
import { useState, useRef } from 'react'

interface AudioRecorderProps {
  onSend: (blob: Blob, duration: number) => void
}

export default function AudioRecorder({ onSend }: AudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  
  const mediaRecorder = useRef<MediaRecorder | null>(null)
  const timerInterval = useRef<ReturnType<typeof setInterval> | null>(null)
  const audioChunks = useRef<Blob[]>([])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaRecorder.current = new MediaRecorder(stream)
      audioChunks.current = []

      mediaRecorder.current.ondataavailable = (event) => {
        audioChunks.current.push(event.data)
      }

      mediaRecorder.current.onstop = () => {
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/wav' })
        setAudioBlob(audioBlob)
      }

      mediaRecorder.current.start()
      setIsRecording(true)
      
      // Start timer
      let seconds = 0
      timerInterval.current = setInterval(() => {
        seconds++
        setRecordingTime(seconds)
      }, 1000)

    } catch (error) {
      console.error('Error accessing microphone:', error)
    }
  }

  const stopRecording = () => {
    if (mediaRecorder.current && isRecording) {
      mediaRecorder.current.stop()
      mediaRecorder.current.stream.getTracks().forEach(track => track.stop())
      setIsRecording(false)
      
      // Clear timer
      if (timerInterval.current) {
        clearInterval(timerInterval.current)
        timerInterval.current = null
      }
    }
  }

  const handleSend = async () => {
    if (audioBlob) {
      setIsProcessing(true)
      await onSend(audioBlob, recordingTime)
      setAudioBlob(null)
      setRecordingTime(0)
      setIsProcessing(false)
    }
  }

  const handleDelete = () => {
    setAudioBlob(null)
    setRecordingTime(0)
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="flex items-center gap-4">
      {!audioBlob ? (
        <button
          onClick={isRecording ? stopRecording : startRecording}
          className="w-10 h-10 rounded-full flex items-center justify-center bg-red-500 hover:bg-red-600 transition-all"
          disabled={isProcessing}
        >
          {isRecording ? (
            <span className="text-white text-sm font-mono">
              {formatTime(recordingTime)}
            </span>
          ) : (
            <svg 
              viewBox="0 0 24 24" 
              className="w-6 h-6 text-white"
              fill="currentColor"
            >
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
            </svg>
          )}
        </button>
      ) : (
        <div className="flex items-center gap-3">
          <button
            onClick={handleDelete}
            className="w-10 h-10 rounded-full flex items-center justify-center bg-red-500 hover:bg-red-600 transition-all"
          >
            <svg 
              viewBox="0 0 24 24" 
              className="w-5 h-5 text-white"
              fill="currentColor"
            >
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
          <button
            onClick={handleSend}
            className="w-10 h-10 rounded-full flex items-center justify-center bg-blue-500 hover:bg-blue-600 transition-all"
            disabled={isProcessing}
          >
            <svg 
              viewBox="0 0 24 24" 
              className="w-5 h-5 text-white"
              fill="currentColor"
            >
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </div>
      )}
    </div>
  )
}