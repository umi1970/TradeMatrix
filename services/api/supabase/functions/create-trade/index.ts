// Supabase Edge Function: Create Trade
// Deploy with: supabase functions deploy create-trade

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Get authenticated user
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
      {
        global: {
          headers: { Authorization: req.headers.get('Authorization')! },
        },
      }
    )

    const {
      data: { user },
      error: userError,
    } = await supabaseClient.auth.getUser()

    if (userError || !user) {
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    // Parse request body
    const body = await req.json()
    const { symbol, side, entry_price, position_size, stop_loss, take_profit, notes, tags } = body

    // Validate required fields
    if (!symbol || !side || !entry_price || !position_size) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields: symbol, side, entry_price, position_size' }),
        {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        }
      )
    }

    // Insert trade
    const { data, error } = await supabaseClient
      .from('trades')
      .insert({
        user_id: user.id,
        symbol,
        side,
        entry_price,
        position_size,
        stop_loss,
        take_profit,
        notes,
        tags,
        status: 'open',
      })
      .select()
      .single()

    if (error) {
      throw error
    }

    return new Response(JSON.stringify({ trade: data }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 201,
    })
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 400,
    })
  }
})
