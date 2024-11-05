import { createClient } from '@supabase/supabase-js'
import { Database } from './database.types'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey)

export interface Message {
  id: string;
  message: string;
  transcription: string | null;
  analysis: string | null;
  reply: string | null;
  is_ai: boolean;
  created_at: string;
  user_id: string | null;
  temp_user_id: string | null;
  session_type: 'temporary' | 'logged-in';
  status: 'received' | 'processing' | 'completed' | 'error';
  audio_url?: string;
  audio_data?: string;
  audio_duration?: number;
  audio_format?: string;
  processing_time?: number;
}