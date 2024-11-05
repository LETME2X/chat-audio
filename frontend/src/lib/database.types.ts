export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      messages: {
        Row: {
          id: string
          user_id: string | null
          temp_user_id: string | null
          message: string
          audio_url: string | null
          audio_data: string | null
          transcription: string | null
          ai_response: string | null
          reply: string | null
          status: string | null
          created_at: string | null
          audio_duration: number | null
          audio_format: string | null
          is_ai: boolean | null
          processing_time: number | null
          analysis: string | null
          session_type: string | null
        }
        Insert: {
          id?: string
          user_id?: string | null
          temp_user_id?: string | null
          message: string
          audio_url?: string | null
          audio_data?: string | null
          transcription?: string | null
          ai_response?: string | null
          reply?: string | null
          status?: string | null
          created_at?: string | null
          audio_duration?: number | null
          audio_format?: string | null
          is_ai?: boolean | null
          processing_time?: number | null
          analysis?: string | null
          session_type?: string | null
        }
        Update: {
          id?: string
          user_id?: string | null
          temp_user_id?: string | null
          message?: string
          audio_url?: string | null
          audio_data?: string | null
          transcription?: string | null
          ai_response?: string | null
          reply?: string | null
          status?: string | null
          created_at?: string | null
          audio_duration?: number | null
          audio_format?: string | null
          is_ai?: boolean | null
          processing_time?: number | null
          analysis?: string | null
          session_type?: string | null
        }
      }
    }
  }
}