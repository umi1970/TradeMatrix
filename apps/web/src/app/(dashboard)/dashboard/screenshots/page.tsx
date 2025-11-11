'use client'

import { useState, useEffect } from 'react'
import { Upload, TrendingUp, TrendingDown, Minus, AlertCircle, CheckCircle2, Loader2, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'

interface AnalysisResult {
  file: File | null  // Allow null for existing analyses
  status: 'pending' | 'analyzing' | 'success' | 'error'
  screenshot_url?: string  // For existing analyses from DB
  analysis?: {
    analysis_id: string
    symbol: string
    timeframe: string
    current_price: number
    trend: string
    trend_strength?: string
    price_vs_emas?: string
    momentum_bias?: string
    confidence_score: number
    chart_quality?: string
    key_factors?: string[]
    setup_type: string
    entry_price?: number
    stop_loss?: number
    take_profit?: number
    risk_reward?: number
    reasoning?: string
    detailed_analysis?: string
    timeframe_validity?: string
    patterns_detected?: string[]
    support_levels?: number[]
    resistance_levels?: number[]
  }
  error?: string
}

export default function ScreenshotsPage() {
  const [files, setFiles] = useState<AnalysisResult[]>([])
  const [uploading, setUploading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [creatingSetup, setCreatingSetup] = useState<string | null>(null) // Track which analysis is creating setup

  useEffect(() => {
    loadExistingAnalyses()
  }, [])

  const loadExistingAnalyses = async () => {
    try {
      console.log('📥 Loading existing analyses...')
      // Fetch recent analyses from DB that have screenshot URLs
      const response = await fetch('/api/screenshots/history?limit=50')
      const data = await response.json()

      console.log('📊 History response:', { ok: response.ok, count: data.analyses?.length || 0 })

      if (response.ok && data.analyses) {
        // Convert DB analyses to AnalysisResult format
        const existingAnalyses: AnalysisResult[] = data.analyses
          .filter((dbAnalysis: any) => {
            // Ensure payload exists and has minimum required fields
            return dbAnalysis.payload &&
                   dbAnalysis.payload.current_price &&
                   dbAnalysis.chart_url
          })
          .map((dbAnalysis: any) => {
            const payload = dbAnalysis.payload || {}

            return {
              file: null, // No file object for existing analyses
              status: 'success' as const,
              analysis: {
                analysis_id: dbAnalysis.id,
                symbol: dbAnalysis.market_symbols?.symbol || 'Unknown',
                timeframe: dbAnalysis.timeframe || '5m',
                current_price: payload.current_price || 0,
                trend: dbAnalysis.trend || 'unknown',
                trend_strength: payload.trend_strength,
                price_vs_emas: payload.price_vs_emas,
                momentum_bias: payload.momentum_bias,
                confidence_score: dbAnalysis.confidence_score || 0,
                chart_quality: payload.chart_quality,
                key_factors: payload.key_factors || [],
                setup_type: payload.setup_type || 'no_trade',
                entry_price: payload.entry_price,
                stop_loss: payload.stop_loss,
                take_profit: payload.take_profit,
                risk_reward: payload.risk_reward,
                reasoning: dbAnalysis.analysis_summary || '',
                detailed_analysis: payload.detailed_analysis,
                timeframe_validity: payload.timeframe_validity,
                patterns_detected: dbAnalysis.patterns_detected || [],
                support_levels: dbAnalysis.support_levels || [],
                resistance_levels: dbAnalysis.resistance_levels || [],
              },
              screenshot_url: dbAnalysis.chart_url,
            }
          })

        console.log('✅ Loaded analyses:', existingAnalyses.length)
        setFiles(existingAnalyses)
      }
    } catch (error) {
      console.error('❌ Failed to load existing analyses:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = (selectedFiles: FileList) => {
    const newFiles: AnalysisResult[] = Array.from(selectedFiles).map(file => ({
      file,
      status: 'pending'
    }))
    setFiles(prev => [...prev, ...newFiles])
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    if (e.dataTransfer.files) {
      handleFileSelect(e.dataTransfer.files)
    }
  }

  const analyzeScreenshots = async () => {
    setUploading(true)

    // Get all pending files
    const pendingFiles = files.filter(f => f.status === 'pending' && f.file)

    if (pendingFiles.length === 0) {
      setUploading(false)
      return
    }

    // Mark all as analyzing
    setFiles(prev => prev.map(f =>
      f.status === 'pending' && f.file ? { ...f, status: 'analyzing' as const } : f
    ))

    try {
      // Send ALL files in ONE request
      const formData = new FormData()
      pendingFiles.forEach((item, index) => {
        formData.append(`files`, item.file!) // Multiple files with same key
      })
      formData.append('symbol', 'AUTO') // Let Vision detect symbol

      const response = await fetch('/api/screenshots/analyze', {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (response.ok) {
        // Success - update all pending files with the combined analysis
        setFiles(prev => prev.map(f => {
          if (f.status === 'analyzing') {
            return {
              ...f,
              status: 'success' as const,
              analysis: data,
              screenshot_url: data.screenshot_urls?.[0], // Use first screenshot URL for display
              error: undefined
            }
          }
          return f
        }))
      } else {
        // Error - mark all analyzing files as error
        setFiles(prev => prev.map(f =>
          f.status === 'analyzing' ? { ...f, status: 'error' as const, error: data.error } : f
        ))
      }
    } catch (error) {
      console.error('Network error:', error)
      setFiles(prev => prev.map(f =>
        f.status === 'analyzing' ? { ...f, status: 'error' as const, error: 'Network error' } : f
      ))
    }

    setUploading(false)
  }

  const clearAll = () => {
    setFiles([])
  }

  const handleCreateSetup = async (analysisId: string) => {
    setCreatingSetup(analysisId)
    try {
      const response = await fetch('/api/screenshots/create-setup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ analysis_id: analysisId }),
      })

      const data = await response.json()

      if (response.ok && data.setup_id) {
        console.log('✅ Setup created:', data.setup_id)
        // Redirect to agents page with setup_id
        window.location.href = `/dashboard/agents?highlight=${data.setup_id}`
      } else {
        console.error('Failed to create setup:', data.error)
        alert(`Failed to create setup: ${data.error}`)
      }
    } catch (error) {
      console.error('Error creating setup:', error)
      alert('Failed to create setup. Please try again.')
    } finally {
      setCreatingSetup(null)
    }
  }

  const hasPendingFiles = files.some(f => f.status === 'pending')
  const successCount = files.filter(f => f.status === 'success').length

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'bullish': return <TrendingUp className="h-5 w-5 text-green-500" />
      case 'bearish': return <TrendingDown className="h-5 w-5 text-red-500" />
      default: return <Minus className="h-5 w-5 text-yellow-500" />
    }
  }

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'bullish': return 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300'
      case 'bearish': return 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300'
      default: return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-300'
    }
  }

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Chart Screenshot Analysis</h1>
        <p className="text-muted-foreground">
          Upload trading chart screenshots. OpenAI Vision will analyze them like a professional trader.
        </p>
      </div>

      <Alert className="mb-6">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Upload screenshots from TradingView, MetaTrader, or any trading platform. OPTIONAL: Also upload corresponding CSV files with exact OHLCV + Indicator data for higher precision.
          Vision AI will automatically detect: Symbol, Timeframe, Price, Indicators, Patterns, Support/Resistance, and Trading Setups.
        </AlertDescription>
      </Alert>

      {/* Upload Zone */}
      {files.length === 0 ? (
        <Card className="mb-6">
          <CardContent className="p-12">
            <div
              className="border-2 border-dashed rounded-lg p-12 text-center cursor-pointer hover:border-primary transition-colors"
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              onClick={() => {
                const input = document.createElement('input')
                input.type = 'file'
                input.accept = 'image/*,text/csv,.csv'
                input.multiple = true
                input.onchange = (e) => {
                  const files = (e.target as HTMLInputElement).files
                  if (files) handleFileSelect(files)
                }
                input.click()
              }}
            >
              <Upload className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">Drop screenshots + CSV files here or click to upload</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Screenshots (JPG, PNG, WebP) + Optional CSV files with exact data
              </p>
              <Button>Select Files</Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Action Buttons */}
          <div className="flex justify-between items-center mb-6">
            <div className="text-sm text-muted-foreground">
              {files.length} screenshot{files.length !== 1 ? 's' : ''} uploaded
              {successCount > 0 && ` • ${successCount} analyzed`}
            </div>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => {
                  const input = document.createElement('input')
                  input.type = 'file'
                  input.accept = 'image/*,text/csv,.csv'
                  input.multiple = true
                  input.onchange = (e) => {
                    const files = (e.target as HTMLInputElement).files
                    if (files) handleFileSelect(files)
                  }
                  input.click()
                }}
              >
                Add More
              </Button>
              <Button
                variant="outline"
                onClick={clearAll}
                disabled={uploading}
              >
                Clear All
              </Button>
              <Button
                onClick={analyzeScreenshots}
                disabled={!hasPendingFiles || uploading}
                size="lg"
              >
                {uploading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  `Analyze ${files.filter(f => f.status === 'pending').length} Screenshot${files.filter(f => f.status === 'pending').length !== 1 ? 's' : ''}`
                )}
              </Button>
            </div>
          </div>

          {/* Results Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {files.map((item, index) => (
              <Card key={index} className="relative overflow-hidden">
                {item.status === 'analyzing' && (
                  <div className="absolute inset-0 bg-background/50 backdrop-blur-sm flex items-center justify-center z-10">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                  </div>
                )}

                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-base flex items-center gap-2">
                        {item.status === 'success' && item.analysis && (
                          <>
                            {getTrendIcon(item.analysis.trend)}
                            <span>{item.analysis.symbol}</span>
                            <Badge variant="outline" className="ml-1">
                              {item.analysis.timeframe}
                            </Badge>
                          </>
                        )}
                        {item.status === 'pending' && (
                          <span className="text-muted-foreground">{item.file?.name || 'Unknown'}</span>
                        )}
                        {item.status === 'error' && (
                          <span className="text-destructive">{item.file?.name || 'Unknown'}</span>
                        )}
                      </CardTitle>
                      <CardDescription className="text-xs mt-1">
                        {item.file ? `${(item.file.size / 1024).toFixed(0)} KB` : 'From history'}
                      </CardDescription>
                    </div>

                    {item.status === 'success' && (
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                    )}
                    {item.status === 'error' && (
                      <AlertCircle className="h-5 w-5 text-destructive" />
                    )}
                  </div>
                </CardHeader>

                <CardContent>
                  {item.status === 'success' && item.analysis && (
                    <div className="space-y-3">
                      {/* Screenshot Image */}
                      {(item.screenshot_url || item.file) && (
                        <div className="mb-3 relative">
                          <img
                            src={item.screenshot_url || (item.file ? URL.createObjectURL(item.file) : '')}
                            alt={`Chart ${item.analysis?.symbol}`}
                            className="w-full h-48 object-contain bg-muted rounded"
                            loading="lazy"
                          />
                        </div>
                      )}

                      {/* Price & Trend */}
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-2xl font-bold">{item.analysis.current_price.toLocaleString()}</p>
                          <div className="flex gap-2 mt-1">
                            <Badge className={getTrendColor(item.analysis.trend)}>
                              {item.analysis.trend.toUpperCase()}
                            </Badge>
                            {item.analysis.trend_strength && (
                              <Badge variant="outline" className="text-xs">
                                {item.analysis.trend_strength}
                              </Badge>
                            )}
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-muted-foreground">Confidence</p>
                          <p className="text-lg font-semibold">{(item.analysis.confidence_score * 100).toFixed(0)}%</p>
                          {item.analysis.chart_quality && (
                            <p className="text-xs text-muted-foreground capitalize">{item.analysis.chart_quality}</p>
                          )}
                        </div>
                      </div>

                      {/* Momentum & Price Position */}
                      {(item.analysis.momentum_bias || item.analysis.price_vs_emas) && (
                        <div className="p-2 bg-muted/50 rounded text-xs space-y-1">
                          {item.analysis.momentum_bias && (
                            <p><span className="font-semibold">Momentum:</span> {item.analysis.momentum_bias}</p>
                          )}
                          {item.analysis.price_vs_emas && (
                            <p><span className="font-semibold">Price vs EMAs:</span> {item.analysis.price_vs_emas.replace('_', ' ')}</p>
                          )}
                        </div>
                      )}

                      {/* Patterns & Key Factors */}
                      {(item.analysis.patterns_detected?.length > 0 || item.analysis.key_factors?.length > 0) && (
                        <div className="space-y-2 text-xs">
                          {item.analysis.patterns_detected?.length > 0 && (
                            <div>
                              <p className="font-semibold mb-1">Patterns:</p>
                              <div className="flex flex-wrap gap-1">
                                {item.analysis.patterns_detected.map((pattern, i) => (
                                  <Badge key={i} variant="secondary" className="text-xs">
                                    {pattern}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                          {item.analysis.key_factors?.length > 0 && (
                            <div>
                              <p className="font-semibold mb-1">Key Factors:</p>
                              <ul className="list-disc list-inside text-muted-foreground space-y-0.5">
                                {item.analysis.key_factors.map((factor, i) => (
                                  <li key={i}>{factor}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Setup Recommendation */}
                      {item.analysis.setup_type !== 'no_trade' && (
                        <div className="p-3 bg-muted rounded-lg space-y-2">
                          <div className="text-sm font-semibold flex items-center gap-2">
                            <Badge variant={item.analysis.setup_type === 'long' ? 'default' : 'destructive'}>
                              {item.analysis.setup_type?.toUpperCase()}
                            </Badge>
                            <span>Setup Recommendation</span>
                            {item.analysis.timeframe_validity && (
                              <Badge variant="outline" className="text-xs ml-auto">
                                {item.analysis.timeframe_validity}
                              </Badge>
                            )}
                          </div>
                          {item.analysis.entry_price && (
                            <div className="grid grid-cols-4 gap-2 text-xs">
                              <div>
                                <p className="text-muted-foreground">Entry</p>
                                <p className="font-mono font-semibold">{item.analysis.entry_price.toLocaleString()}</p>
                              </div>
                              <div>
                                <p className="text-muted-foreground">Stop</p>
                                <p className="font-mono font-semibold">{item.analysis.stop_loss?.toLocaleString()}</p>
                              </div>
                              <div>
                                <p className="text-muted-foreground">Target</p>
                                <p className="font-mono font-semibold">{item.analysis.take_profit?.toLocaleString()}</p>
                              </div>
                              <div>
                                <p className="text-muted-foreground">R:R</p>
                                <p className="font-mono font-semibold">
                                  {typeof item.analysis.risk_reward === 'number'
                                    ? item.analysis.risk_reward.toFixed(1)
                                    : item.analysis.risk_reward || 'N/A'}
                                </p>
                              </div>
                            </div>
                          )}
                          {item.analysis.reasoning && (
                            <p className="text-xs text-muted-foreground pt-2 border-t">
                              {item.analysis.reasoning}
                            </p>
                          )}
                        </div>
                      )}

                      {/* Generate Setup Button */}
                      {item.analysis.setup_type === 'no_trade' ? (
                        <Alert className="border-amber-200 bg-amber-50 dark:bg-amber-950/20">
                          <AlertCircle className="h-4 w-4 text-amber-600" />
                          <AlertDescription className="text-amber-900 dark:text-amber-200">
                            No valid trade setup detected in this analysis
                          </AlertDescription>
                        </Alert>
                      ) : (
                        <Button
                          className="w-full"
                          variant="outline"
                          onClick={() => handleCreateSetup(item.analysis!.analysis_id)}
                          disabled={creatingSetup === item.analysis?.analysis_id}
                        >
                          {creatingSetup === item.analysis?.analysis_id ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Creating Setup...
                            </>
                          ) : (
                            <>
                              Generate Trading Setup
                              <ArrowRight className="ml-2 h-4 w-4" />
                            </>
                          )}
                        </Button>
                      )}
                    </div>
                  )}

                  {item.status === 'error' && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{item.error}</AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
