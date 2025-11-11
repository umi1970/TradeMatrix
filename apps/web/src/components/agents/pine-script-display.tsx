'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Copy, Check, Code2, ExternalLink } from 'lucide-react'

interface PineScriptDisplayProps {
  pineScript: string
  active?: boolean
  ticker: string
  setupId: string
}

export function PineScriptDisplay({ pineScript, active = false, ticker, setupId }: PineScriptDisplayProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(pineScript)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <Card className="border-2 border-blue-500/20">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Code2 className="h-4 w-4 text-blue-500" />
              <CardTitle className="text-base">Pine Script Monitor</CardTitle>
              {active && (
                <Badge variant="outline" className="bg-green-500/20 text-green-700 dark:text-green-400 border-green-500/50">
                  Active
                </Badge>
              )}
            </div>
            <CardDescription className="text-xs">
              Paste this code in TradingView Pine Editor to monitor Entry/SL/TP levels
            </CardDescription>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={handleCopy}
            className="shrink-0"
          >
            {copied ? (
              <>
                <Check className="h-3 w-3 mr-1" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="h-3 w-3 mr-1" />
                Copy Code
              </>
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Pine Script Code Preview */}
        <div className="relative">
          <div className="bg-muted/50 rounded-md p-3 max-h-64 overflow-y-auto">
            <pre className="text-xs font-mono text-muted-foreground whitespace-pre-wrap">
              {pineScript}
            </pre>
          </div>
        </div>

        {/* Instructions */}
        <div className="space-y-2 text-xs text-muted-foreground">
          <p className="font-semibold text-foreground">Setup Instructions:</p>
          <ol className="list-decimal list-inside space-y-1">
            <li>Open TradingView and navigate to <strong>{ticker}</strong> chart</li>
            <li>Click "Pine Editor" in the bottom panel</li>
            <li>Click "Copy Code" button above, then paste in Pine Editor</li>
            <li>Click "Add to Chart" (or Ctrl/Cmd + S)</li>
            <li>Create 3 alerts: <code>entryHit</code>, <code>slHit</code>, <code>tpHit</code></li>
            <li>Set webhook URL in alert settings (provided in script)</li>
          </ol>
        </div>

        {/* TradingView Link */}
        <div className="pt-2 border-t">
          <a
            href={`https://www.tradingview.com/chart/?symbol=${ticker}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            <ExternalLink className="h-3 w-3" />
            Open {ticker} in TradingView
          </a>
        </div>

        {/* Setup ID Reference */}
        <div className="text-xs text-muted-foreground">
          <span className="font-semibold">Setup ID:</span>{' '}
          <code className="bg-muted px-1 py-0.5 rounded">{setupId}</code>
        </div>
      </CardContent>
    </Card>
  )
}
