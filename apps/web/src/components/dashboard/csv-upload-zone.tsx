'use client'

import { useState, useCallback, DragEvent } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Loader2, Upload, FileText, CheckCircle2, XCircle, TrendingUp, TrendingDown } from 'lucide-react'

interface AnalysisResult {
  analysis_id: string
  symbol: string
  timeframe: string
  current_price: number
  trend: string
  trend_strength?: string
  confidence_score: number
  setup_type: string
  entry_price?: number
  stop_loss?: number
  take_profit?: number
  risk_reward?: number
  reasoning: string
  csv_url: string
}

export function CSVUploadZone() {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)

  // Handle drag events
  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    const csvFile = files.find(file => file.name.endsWith('.csv'))

    if (csvFile) {
      setSelectedFile(csvFile)
      setError(null)
      setAnalysis(null)
    } else {
      setError('Please drop a CSV file')
    }
  }, [])

  // Handle file input change
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && file.name.endsWith('.csv')) {
      setSelectedFile(file)
      setError(null)
      setAnalysis(null)
    } else {
      setError('Please select a CSV file')
    }
  }

  // Upload and parse CSV
  const handleUpload = async () => {
    if (!selectedFile) {
      setError('No file selected')
      return
    }

    setIsUploading(true)
    setError(null)
    setAnalysis(null)

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      // Extract symbol from filename if possible (e.g., "CAPITALCOM_US30, 15.csv" -> "US30")
      const symbolMatch = selectedFile.name.match(/[A-Z]+\d+/)
      if (symbolMatch) {
        formData.append('symbol', symbolMatch[0])
      }

      const response = await fetch('/api/charts/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to upload CSV')
      }

      const result: AnalysisResult = await response.json()
      setAnalysis(result)
      setSelectedFile(null)

    } catch (err) {
      console.error('Upload error:', err)
      setError(err instanceof Error ? err.message : 'Failed to upload CSV')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Upload Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            TradingView CSV Upload
          </CardTitle>
          <CardDescription>
            Upload your TradingView chart export (CSV) for AI-powered analysis
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Drag-and-Drop Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`
              border-2 border-dashed rounded-lg p-8 text-center transition-colors
              ${isDragging ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'}
              ${selectedFile ? 'bg-accent/50' : 'bg-muted/20'}
            `}
          >
            {selectedFile ? (
              <div className="space-y-3">
                <FileText className="h-12 w-12 mx-auto text-primary" />
                <div>
                  <p className="font-medium">{selectedFile.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
                <Button
                  onClick={() => setSelectedFile(null)}
                  variant="outline"
                  size="sm"
                >
                  Remove
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                <Upload className="h-12 w-12 mx-auto text-muted-foreground" />
                <div>
                  <p className="font-medium">Drag and drop your CSV file here</p>
                  <p className="text-sm text-muted-foreground">or click to browse</p>
                </div>
                <label htmlFor="csv-upload">
                  <Button variant="outline" size="sm" asChild>
                    <span>Browse Files</span>
                  </Button>
                  <input
                    id="csv-upload"
                    type="file"
                    accept=".csv"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </label>
              </div>
            )}
          </div>

          {/* Upload Button */}
          {selectedFile && (
            <Button
              onClick={handleUpload}
              disabled={isUploading}
              className="w-full"
            >
              {isUploading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing CSV...
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload and Analyze
                </>
              )}
            </Button>
          )}

          {/* Error Alert */}
          {error && (
            <Alert variant="destructive">
              <XCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Analysis Results */}
      {analysis && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              Analysis Complete
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Market Info */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Symbol</p>
                <p className="text-lg font-bold">{analysis.symbol}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Timeframe</p>
                <p className="text-lg font-bold">{analysis.timeframe}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Current Price</p>
                <p className="text-lg font-bold">{analysis.current_price.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Confidence</p>
                <p className="text-lg font-bold">{(analysis.confidence_score * 100).toFixed(0)}%</p>
              </div>
            </div>

            {/* Trend & Setup */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <p className="text-sm font-medium">Trend</p>
                <div className="flex items-center gap-2">
                  {analysis.trend === 'bullish' ? (
                    <TrendingUp className="h-5 w-5 text-green-500" />
                  ) : analysis.trend === 'bearish' ? (
                    <TrendingDown className="h-5 w-5 text-red-500" />
                  ) : (
                    <div className="h-5 w-5" />
                  )}
                  <Badge variant={analysis.trend === 'bullish' ? 'default' : analysis.trend === 'bearish' ? 'destructive' : 'secondary'}>
                    {analysis.trend.toUpperCase()}
                    {analysis.trend_strength && ` (${analysis.trend_strength})`}
                  </Badge>
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-sm font-medium">Setup Type</p>
                <Badge variant={analysis.setup_type === 'no_trade' ? 'outline' : 'default'}>
                  {analysis.setup_type.toUpperCase()}
                </Badge>
              </div>
            </div>

            {/* Trading Levels */}
            {analysis.setup_type !== 'no_trade' && analysis.entry_price && (
              <div className="space-y-2">
                <p className="text-sm font-medium">Trading Levels</p>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 bg-accent/30 p-4 rounded-lg">
                  <div>
                    <p className="text-xs text-muted-foreground">Entry</p>
                    <p className="font-mono font-bold text-blue-600">{analysis.entry_price.toFixed(2)}</p>
                  </div>
                  {analysis.stop_loss && (
                    <div>
                      <p className="text-xs text-muted-foreground">Stop Loss</p>
                      <p className="font-mono font-bold text-red-600">{analysis.stop_loss.toFixed(2)}</p>
                    </div>
                  )}
                  {analysis.take_profit && (
                    <div>
                      <p className="text-xs text-muted-foreground">Take Profit</p>
                      <p className="font-mono font-bold text-green-600">{analysis.take_profit.toFixed(2)}</p>
                    </div>
                  )}
                  {analysis.risk_reward && (
                    <div>
                      <p className="text-xs text-muted-foreground">R:R</p>
                      <p className="font-mono font-bold">{analysis.risk_reward.toFixed(2)}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Reasoning */}
            <div className="space-y-2">
              <p className="text-sm font-medium">AI Analysis</p>
              <div className="bg-muted/50 p-4 rounded-lg">
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {analysis.reasoning}
                </p>
              </div>
            </div>

            {/* CSV Link */}
            <div className="flex items-center justify-between pt-2 border-t">
              <p className="text-xs text-muted-foreground">
                Analysis ID: {analysis.analysis_id}
              </p>
              <Button variant="outline" size="sm" asChild>
                <a href={analysis.csv_url} target="_blank" rel="noopener noreferrer">
                  View CSV
                </a>
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
