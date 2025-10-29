/**
 * TypeScript Database Types for Supabase
 *
 * These types are generated from the database schema.
 * They provide type safety for Supabase queries.
 *
 * To regenerate types (when schema changes):
 * 1. Install Supabase CLI: npm install -g supabase
 * 2. Login: supabase login
 * 3. Link project: supabase link --project-ref YOUR_PROJECT_REF
 * 4. Generate types: supabase gen types typescript --local > src/lib/supabase/types.ts
 *
 * For now, these are manually created based on the schema.
 */

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
      profiles: {
        Row: {
          id: string
          email: string
          full_name: string | null
          avatar_url: string | null
          subscription_tier: 'free' | 'starter' | 'pro' | 'expert'
          subscription_status: 'active' | 'cancelled' | 'past_due' | 'trialing'
          stripe_customer_id: string | null
          stripe_subscription_id: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id: string
          email: string
          full_name?: string | null
          avatar_url?: string | null
          subscription_tier?: 'free' | 'starter' | 'pro' | 'expert'
          subscription_status?: 'active' | 'cancelled' | 'past_due' | 'trialing'
          stripe_customer_id?: string | null
          stripe_subscription_id?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          email?: string
          full_name?: string | null
          avatar_url?: string | null
          subscription_tier?: 'free' | 'starter' | 'pro' | 'expert'
          subscription_status?: 'active' | 'cancelled' | 'past_due' | 'trialing'
          stripe_customer_id?: string | null
          stripe_subscription_id?: string | null
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: 'profiles_id_fkey'
            columns: ['id']
            referencedRelation: 'users'
            referencedColumns: ['id']
          }
        ]
      }
      trades: {
        Row: {
          id: string
          user_id: string
          symbol: string
          side: 'long' | 'short'
          entry_price: number
          exit_price: number | null
          position_size: number
          stop_loss: number | null
          take_profit: number | null
          status: 'open' | 'closed' | 'cancelled'
          pnl: number | null
          pnl_percentage: number | null
          entry_time: string
          exit_time: string | null
          notes: string | null
          tags: string[] | null
          metadata: Json
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          symbol: string
          side: 'long' | 'short'
          entry_price: number
          exit_price?: number | null
          position_size: number
          stop_loss?: number | null
          take_profit?: number | null
          status?: 'open' | 'closed' | 'cancelled'
          pnl?: number | null
          pnl_percentage?: number | null
          entry_time?: string
          exit_time?: string | null
          notes?: string | null
          tags?: string[] | null
          metadata?: Json
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          symbol?: string
          side?: 'long' | 'short'
          entry_price?: number
          exit_price?: number | null
          position_size?: number
          stop_loss?: number | null
          take_profit?: number | null
          status?: 'open' | 'closed' | 'cancelled'
          pnl?: number | null
          pnl_percentage?: number | null
          entry_time?: string
          exit_time?: string | null
          notes?: string | null
          tags?: string[] | null
          metadata?: Json
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: 'trades_user_id_fkey'
            columns: ['user_id']
            referencedRelation: 'profiles'
            referencedColumns: ['id']
          }
        ]
      }
      reports: {
        Row: {
          id: string
          user_id: string
          title: string
          content: string
          report_type: 'daily' | 'weekly' | 'analysis' | 'custom'
          ai_summary: string | null
          ai_insights: Json
          status: 'draft' | 'published' | 'archived'
          published_at: string | null
          slug: string | null
          chart_urls: string[] | null
          pdf_url: string | null
          metadata: Json
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          title: string
          content: string
          report_type: 'daily' | 'weekly' | 'analysis' | 'custom'
          ai_summary?: string | null
          ai_insights?: Json
          status?: 'draft' | 'published' | 'archived'
          published_at?: string | null
          slug?: string | null
          chart_urls?: string[] | null
          pdf_url?: string | null
          metadata?: Json
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          title?: string
          content?: string
          report_type?: 'daily' | 'weekly' | 'analysis' | 'custom'
          ai_summary?: string | null
          ai_insights?: Json
          status?: 'draft' | 'published' | 'archived'
          published_at?: string | null
          slug?: string | null
          chart_urls?: string[] | null
          pdf_url?: string | null
          metadata?: Json
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: 'reports_user_id_fkey'
            columns: ['user_id']
            referencedRelation: 'profiles'
            referencedColumns: ['id']
          }
        ]
      }
      agent_logs: {
        Row: {
          id: string
          user_id: string | null
          agent_type: 'chart_watcher' | 'signal_bot' | 'risk_manager' | 'journal_bot' | 'publisher'
          task_id: string | null
          status: 'running' | 'completed' | 'failed'
          input_data: Json | null
          output_data: Json | null
          error_message: string | null
          started_at: string
          completed_at: string | null
          duration_ms: number | null
          created_at: string
        }
        Insert: {
          id?: string
          user_id?: string | null
          agent_type: 'chart_watcher' | 'signal_bot' | 'risk_manager' | 'journal_bot' | 'publisher'
          task_id?: string | null
          status?: 'running' | 'completed' | 'failed'
          input_data?: Json | null
          output_data?: Json | null
          error_message?: string | null
          started_at?: string
          completed_at?: string | null
          duration_ms?: number | null
          created_at?: string
        }
        Update: {
          id?: string
          user_id?: string | null
          agent_type?: 'chart_watcher' | 'signal_bot' | 'risk_manager' | 'journal_bot' | 'publisher'
          task_id?: string | null
          status?: 'running' | 'completed' | 'failed'
          input_data?: Json | null
          output_data?: Json | null
          error_message?: string | null
          started_at?: string
          completed_at?: string | null
          duration_ms?: number | null
          created_at?: string
        }
        Relationships: [
          {
            foreignKeyName: 'agent_logs_user_id_fkey'
            columns: ['user_id']
            referencedRelation: 'profiles'
            referencedColumns: ['id']
          }
        ]
      }
      subscriptions: {
        Row: {
          id: string
          user_id: string
          stripe_subscription_id: string
          stripe_customer_id: string
          stripe_price_id: string
          tier: 'starter' | 'pro' | 'expert'
          status: string
          current_period_start: string | null
          current_period_end: string | null
          cancel_at_period_end: boolean
          cancelled_at: string | null
          metadata: Json
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          stripe_subscription_id: string
          stripe_customer_id: string
          stripe_price_id: string
          tier: 'starter' | 'pro' | 'expert'
          status: string
          current_period_start?: string | null
          current_period_end?: string | null
          cancel_at_period_end?: boolean
          cancelled_at?: string | null
          metadata?: Json
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          stripe_subscription_id?: string
          stripe_customer_id?: string
          stripe_price_id?: string
          tier?: 'starter' | 'pro' | 'expert'
          status?: string
          current_period_start?: string | null
          current_period_end?: string | null
          cancel_at_period_end?: boolean
          cancelled_at?: string | null
          metadata?: Json
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: 'subscriptions_user_id_fkey'
            columns: ['user_id']
            referencedRelation: 'profiles'
            referencedColumns: ['id']
          }
        ]
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}
