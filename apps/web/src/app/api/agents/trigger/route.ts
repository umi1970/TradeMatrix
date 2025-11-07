import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // Forward request to FastAPI server (Hetzner Production)
    const response = await fetch('http://135.181.195.241:8000/api/agents/trigger', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    const data = await response.json()

    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error('Error triggering agent:', error)
    return NextResponse.json(
      { error: 'Failed to trigger agent' },
      { status: 500 }
    )
  }
}
