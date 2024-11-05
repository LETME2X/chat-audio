'use client'

import { useAuth } from '@/lib/context/AuthContext'
import { FaGoogle } from 'react-icons/fa'

interface LoginModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function LoginModal({ isOpen, onClose }: LoginModalProps) {
  const { signInWithGoogle } = useAuth()

  if (!isOpen) return null

  const handleSignIn = async () => {
    try {
      await signInWithGoogle()
      onClose()
    } catch (error) {
      console.error('Sign in failed:', error)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full m-4">
        <h2 className="text-2xl font-bold mb-4">Sign In</h2>
        <p className="mb-6 text-gray-600">
          Sign in to get unlimited chats and save your conversation history
        </p>
        <button
          onClick={handleSignIn}
          className="w-full flex items-center justify-center gap-2 bg-white border border-gray-300 text-gray-700 py-3 px-4 rounded hover:bg-gray-50"
        >
          <FaGoogle className="text-red-500" />
          Continue with Google
        </button>
        <button
          onClick={onClose}
          className="w-full mt-4 text-gray-600 hover:text-gray-800"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}