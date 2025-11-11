'use client'

import { useState } from 'react'
import { CSVUploadZone } from '@/components/dashboard/csv-upload-zone'
import { AnalysesTable } from '@/components/dashboard/analyses-table'
import { CSVChartViewer } from '@/components/dashboard/csv-chart-viewer'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Upload, LineChart } from 'lucide-react'

interface CSVChartData {
  symbol: string
  timeframe: string
  current_price: number
  trend: string
  confidence_score: number
  csv_data?: Array<{
    time: string
    open: number
    high: number
    low: number
    close: number
    volume?: number
  }>
}

export default function ChartsPage() {
  const [csvChartData, setCSVChartData] = useState<CSVChartData | null>(null)

  // Handle CSV upload complete
  const handleCSVAnalysisComplete = (analysis: any) => {
    if (analysis.ohlcv_data) {
      setCSVChartData({
        symbol: analysis.symbol,
        timeframe: analysis.timeframe,
        current_price: analysis.current_price,
        trend: analysis.trend,
        confidence_score: analysis.confidence_score,
        csv_data: analysis.ohlcv_data,
      })
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Charts</h1>
        <p className="text-muted-foreground mt-1">
          Analyze market trends with advanced charting tools
        </p>
      </div>

      {/* Tabs: CSV Upload vs Live Charts */}
      <Tabs defaultValue="csv-upload" className="space-y-4">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="csv-upload" className="flex items-center gap-2">
            <Upload className="h-4 w-4" />
            CSV Upload
          </TabsTrigger>
          <TabsTrigger value="live-charts" className="flex items-center gap-2">
            <LineChart className="h-4 w-4" />
            Live Charts
          </TabsTrigger>
        </TabsList>

        {/* CSV Upload Tab */}
        <TabsContent value="csv-upload" className="space-y-4">
          <CSVUploadZone onAnalysisComplete={handleCSVAnalysisComplete} />
          <AnalysesTable />
        </TabsContent>

        {/* Live Charts Tab */}
        <TabsContent value="live-charts" className="space-y-4">
          {/* CSV Chart Viewer - Shows uploaded CSV data only */}
          <CSVChartViewer data={csvChartData} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
