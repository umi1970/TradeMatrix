'use client'

import { useState } from 'react'
import { Upload, TrendingUp, DollarSign, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface UploadZone {
  symbol: string
  displayName: string
  file: File | null
  uploading: boolean
  result: {
    price?: number
    timestamp?: string
    confidence?: number
  } | null
  error?: string
}

export default function ScreenshotsPage() {
  const [zones, setZones] = useState<UploadZone[]>([
    { symbol: 'DAX', displayName: 'DAX 40', file: null, uploading: false, result: null },
    { symbol: 'NDX', displayName: 'NASDAQ 100', file: null, uploading: false, result: null },
    { symbol: 'DJI', displayName: 'Dow Jones', file: null, uploading: false, result: null },
    { symbol: 'EUR/USD', displayName: 'EUR/USD', file: null, uploading: false, result: null },
    { symbol: 'EUR/GBP', displayName: 'EUR/GBP', file: null, uploading: false, result: null },
    { symbol: 'XAG/USD', displayName: 'Silver', file: null, uploading: false, result: null },
  ])

  const [uploading, setUploading] = useState(false)

  const handleFileSelect = (index: number, file: File) => {
    const newZones = [...zones]
    newZones[index].file = file
    newZones[index].error = undefined
    setZones(newZones)
  }

  const handleDrop = (index: number, e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file && file.type.startsWith('image/')) {
      handleFileSelect(index, file)
    }
  }

  const analyzeScreenshots = async () => {
    setUploading(true)

    // Process each zone that has a file
    for (let i = 0; i < zones.length; i++) {
      if (!zones[i].file) continue

      const newZones = [...zones]
      newZones[i].uploading = true
      setZones(newZones)

      try {
        const formData = new FormData()
        formData.append('file', zones[i].file!)
        formData.append('symbol', zones[i].symbol)

        const response = await fetch('/api/screenshots/analyze', {
          method: 'POST',
          body: formData,
        })

        const data = await response.json()

        newZones[i].uploading = false

        if (response.ok) {
          newZones[i].result = {
            price: data.price,
            timestamp: data.timestamp,
            confidence: data.confidence,
          }
          newZones[i].error = undefined
        } else {
          newZones[i].error = data.error || 'Failed to analyze screenshot'
        }

        setZones(newZones)
      } catch (error) {
        newZones[i].uploading = false
        newZones[i].error = 'Network error'
        setZones(newZones)
      }
    }

    setUploading(false)
  }

  const hasFiles = zones.some(z => z.file !== null)

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Screenshot Upload</h1>
        <p className="text-muted-foreground">
          Upload screenshots of current market prices from TradingView or other platforms.
          OpenAI Vision will extract the price data automatically.
        </p>
      </div>

      <Alert className="mb-6">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          <strong>Tip:</strong> Take screenshots that clearly show the symbol name, current price, and timestamp.
          The better the screenshot quality, the more accurate the extraction.
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {zones.map((zone, index) => (
          <Card key={zone.symbol} className="relative">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                {zone.displayName}
              </CardTitle>
              <CardDescription>{zone.symbol}</CardDescription>
            </CardHeader>
            <CardContent>
              <div
                className={`
                  border-2 border-dashed rounded-lg p-6 text-center
                  transition-colors cursor-pointer
                  ${zone.file ? 'border-green-500 bg-green-50 dark:bg-green-950' : 'border-border hover:border-primary'}
                  ${zone.uploading ? 'opacity-50 cursor-wait' : ''}
                `}
                onDrop={(e) => handleDrop(index, e)}
                onDragOver={(e) => e.preventDefault()}
                onClick={() => {
                  const input = document.createElement('input')
                  input.type = 'file'
                  input.accept = 'image/*'
                  input.onchange = (e) => {
                    const file = (e.target as HTMLInputElement).files?.[0]
                    if (file) handleFileSelect(index, file)
                  }
                  input.click()
                }}
              >
                {zone.file ? (
                  <div>
                    <p className="text-sm font-medium text-green-700 dark:text-green-300 mb-1">
                      {zone.file.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {(zone.file.size / 1024).toFixed(0)} KB
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-2">
                    <Upload className="h-8 w-8 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">
                      Drop screenshot here or click to upload
                    </p>
                  </div>
                )}

                {zone.uploading && (
                  <div className="absolute inset-0 flex items-center justify-center bg-background/50">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                )}
              </div>

              {zone.result && (
                <div className="mt-4 p-3 bg-green-50 dark:bg-green-950 rounded-lg">
                  <p className="text-sm font-medium text-green-900 dark:text-green-100 flex items-center gap-2">
                    <DollarSign className="h-4 w-4" />
                    Price: {zone.result.price}
                  </p>
                  {zone.result.timestamp && (
                    <p className="text-xs text-muted-foreground mt-1">
                      {new Date(zone.result.timestamp).toLocaleString()}
                    </p>
                  )}
                  {zone.result.confidence && (
                    <p className="text-xs text-muted-foreground">
                      Confidence: {(zone.result.confidence * 100).toFixed(0)}%
                    </p>
                  )}
                </div>
              )}

              {zone.error && (
                <div className="mt-4 p-3 bg-red-50 dark:bg-red-950 rounded-lg">
                  <p className="text-sm text-red-900 dark:text-red-100">{zone.error}</p>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="flex justify-end gap-4">
        <Button
          variant="outline"
          onClick={() => {
            setZones(zones.map(z => ({ ...z, file: null, result: null, error: undefined })))
          }}
          disabled={!hasFiles || uploading}
        >
          Clear All
        </Button>
        <Button
          onClick={analyzeScreenshots}
          disabled={!hasFiles || uploading}
          size="lg"
        >
          {uploading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Analyzing...
            </>
          ) : (
            'Analyze Screenshots'
          )}
        </Button>
      </div>
    </div>
  )
}
