'use client'

interface ErrorAlertProps {
  message: string
  onClose: () => void
}

export default function ErrorAlert({ message, onClose }: ErrorAlertProps) {
  return (
    <div className="fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded flex items-center gap-2">
      <span className="block sm:inline">{message}</span>
      <button 
        onClick={onClose}
        className="bg-red-200 rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-300 transition-colors"
      >
        ×
      </button>
    </div>
  )
}