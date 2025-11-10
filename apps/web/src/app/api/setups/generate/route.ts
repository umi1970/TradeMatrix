import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // Forward request to FastAPI server
    const response = await fetch('http://135.181.195.241:8000/api/setups/generate-from-analysis', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Setup generation failed', details: data },
        { status: response.status }
      )
    }

    return NextResponse.json(data, { status: 200 })
  } catch (error) {
    console.error('Error generating setup:', error)
    return NextResponse.json(
      { error: 'Failed to generate setup' },
      { status: 500 }
    )
  }
}
