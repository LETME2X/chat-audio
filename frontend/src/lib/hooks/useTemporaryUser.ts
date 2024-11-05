import { useState, useEffect } from 'react'
import { v4 as uuidv4 } from 'uuid'

export function useTemporaryUser() {
  const [tempUserId, setTempUserId] = useState<string | null>(null)

  useEffect(() => {
    const storedId = localStorage.getItem('tempUserId')
    if (storedId) {
      setTempUserId(storedId)
    } else {
      const newId = uuidv4()
      localStorage.setItem('tempUserId', newId)
      setTempUserId(newId)
    }
  }, [])

  return tempUserId
}