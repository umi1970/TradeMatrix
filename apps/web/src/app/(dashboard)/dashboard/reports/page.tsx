'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { createBrowserClient } from '@/lib/supabase/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  FileText,
  Download,
  Filter,
  Eye,
  Trash2,
  Calendar,
  TrendingUp,
  AlertCircle,
  FileJson,
  File,
  Zap,
} from 'lucide-react'

interface Report {
  id: string
  user_id: string
  title: string
  type: 'daily' | 'weekly' | 'monthly' | 'trade_analysis' | 'risk_assessment'
  status: 'completed' | 'processing' | 'failed'
  ai_insights: string
  summary?: string
  metrics?: Record<string, any>
  generated_at: string
  file_url?: string
  docx_url?: string
}

export default function ReportsPage() {
  const router = useRouter()
  const supabase = createBrowserClient()

  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)

  // Filters
  const [dateFilter, setDateFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')

  // Load reports
  useEffect(() => {
    const loadReports = async () => {
      try {
        const {
          data: { user },
        } = await supabase.auth.getUser()

        if (!user) {
          router.push('/login')
          return
        }

        // Fetch reports from Supabase
        // Show: System reports (user_id = NULL) + User's own reports
        const { data: reportsData, error: reportsError } = await (supabase as any)
          .from('reports')
          .select('*')
          .or(`user_id.is.null,user_id.eq.${user.id}`)
          .eq('status', 'completed')
          .order('created_at', { ascending: false })

        if (reportsError) {
          console.error('Error fetching reports:', reportsError)
          setError(`Failed to load reports: ${reportsError.message}`)
          setLoading(false)
          return
        }

        // Transform DB data to frontend format
        const transformedReports: Report[] = (reportsData || []).map((r: any) => ({
          id: r.id,
          user_id: r.user_id,
          title: r.title,
          type: r.report_type,
          status: r.status,
          ai_insights: r.ai_summary || 'No AI insights available',
          summary: r.ai_summary,
          metrics: r.metrics || {},
          generated_at: r.created_at,
          file_url: r.pdf_url,
          docx_url: r.metadata?.file_url_docx || null,
        }))

        setReports(transformedReports)
        setLoading(false)
      } catch (err) {
        console.error('Error loading reports:', err)
        setError('Failed to load reports')
        setLoading(false)
      }
    }

    loadReports()
  }, [supabase, router])

  // Filter reports
  const filteredReports = reports.filter((report) => {
    let matches = true

    // Search filter
    if (searchQuery) {
      matches =
        matches &&
        (report.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          report.ai_insights.toLowerCase().includes(searchQuery.toLowerCase()))
    }

    // Type filter
    if (typeFilter !== 'all') {
      matches = matches && report.type === typeFilter
    }

    // Date filter
    if (dateFilter) {
      const reportDate = new Date(report.generated_at).toISOString().split('T')[0]
      matches = matches && reportDate === dateFilter
    }

    return matches
  })

  const handleGenerateReport = async () => {
    setGenerating(true)
    setError(null)

    try {
      const response = await fetch('/api/reports/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          report_type: 'daily',
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to generate report')
      }

      // Refresh reports list to show the new 'processing' report
      const { data: reportsData } = await (supabase as any)
        .from('reports')
        .select('*')
        .order('created_at', { ascending: false })

      if (reportsData) {
        const transformedReports: Report[] = reportsData.map((r: any) => ({
          id: r.id,
          user_id: r.user_id,
          title: r.title,
          type: r.report_type,
          status: r.status,
          ai_insights: r.ai_summary || 'Processing...',
          summary: r.ai_summary,
          metrics: r.metrics || {},
          generated_at: r.created_at,
          file_url: r.pdf_url,
          docx_url: r.metadata?.file_url_docx || null,
        }))
        setReports(transformedReports)
      }

      // Show success message
      console.log('Report generation started:', data.report_id)
    } catch (err: any) {
      console.error('Error generating report:', err)
      setError(err.message || 'Failed to generate report')
    } finally {
      setGenerating(false)
    }
  }

  const handleDeleteReport = async (reportId: string) => {
    try {
      // Delete from Supabase
      const { error: deleteError } = await (supabase as any)
        .from('reports')
        .delete()
        .eq('id', reportId)

      if (deleteError) {
        throw new Error(deleteError.message)
      }

      // Update local state
      setReports(reports.filter((r) => r.id !== reportId))
    } catch (err: any) {
      console.error('Error deleting report:', err)
      setError(`Failed to delete report: ${err.message}`)
    }
  }

  const downloadReport = (report: Report, format: 'pdf' | 'docx' | 'json') => {
    const filename = `${report.title.replace(/\s+/g, '_')}.${format}`

    if (format === 'json') {
      // Export report as JSON
      const jsonData = JSON.stringify(report, null, 2)
      const blob = new Blob([jsonData], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      link.click()
      URL.revokeObjectURL(url)
    } else if (format === 'pdf') {
      // Download PDF from Supabase Storage
      if (report.file_url) {
        window.open(report.file_url, '_blank')
      } else {
        setError('PDF not available for this report')
      }
    } else if (format === 'docx') {
      // Download DOCX from Supabase Storage
      if (report.docx_url) {
        window.open(report.docx_url, '_blank')
      } else {
        setError('DOCX not available for this report')
      }
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'daily':
        return <Calendar className="h-4 w-4" />
      case 'weekly':
        return <TrendingUp className="h-4 w-4" />
      case 'monthly':
        return <FileText className="h-4 w-4" />
      case 'risk_assessment':
        return <AlertCircle className="h-4 w-4" />
      case 'trade_analysis':
        return <Zap className="h-4 w-4" />
      default:
        return <FileText className="h-4 w-4" />
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'daily':
        return 'bg-blue-100 text-blue-800'
      case 'weekly':
        return 'bg-purple-100 text-purple-800'
      case 'monthly':
        return 'bg-green-100 text-green-800'
      case 'risk_assessment':
        return 'bg-red-100 text-red-800'
      case 'trade_analysis':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'processing':
        return 'bg-yellow-100 text-yellow-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <p className="text-muted-foreground">Loading reports...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Reports</h1>
          <p className="text-muted-foreground mt-1">
            AI-generated trading reports and performance analysis
          </p>
        </div>
        <Button onClick={handleGenerateReport} disabled={generating}>
          <FileText className="h-4 w-4 mr-2" />
          {generating ? 'Generating...' : 'Generate Report'}
        </Button>
      </div>

      {/* Alerts */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Filters */}
      <Card className="bg-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div>
              <label className="text-sm font-medium">Search Reports</label>
              <Input
                placeholder="Search by title or insights..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="mt-2"
              />
            </div>

            {/* Type Filter */}
            <div>
              <label className="text-sm font-medium">Report Type</label>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="mt-2 w-full h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                <option value="all">All Types</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="trade_analysis">Trade Analysis</option>
                <option value="risk_assessment">Risk Assessment</option>
              </select>
            </div>

            {/* Date Filter */}
            <div>
              <label className="text-sm font-medium">Date</label>
              <Input
                type="date"
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
                className="mt-2"
              />
            </div>
          </div>

          {(searchQuery || typeFilter !== 'all' || dateFilter) && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSearchQuery('')
                setTypeFilter('all')
                setDateFilter('')
              }}
            >
              Clear Filters
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Reports List */}
      <div className="space-y-4">
        {filteredReports.length === 0 ? (
          <Card>
            <CardContent className="py-12">
              <div className="text-center space-y-4">
                <FileText className="h-12 w-12 mx-auto text-muted-foreground" />
                <div>
                  <p className="font-medium">No reports found</p>
                  <p className="text-sm text-muted-foreground">
                    {reports.length === 0
                      ? 'Generate your first trading report to get started.'
                      : 'No reports match your filters.'}
                  </p>
                </div>
                {reports.length === 0 && (
                  <Button onClick={handleGenerateReport} disabled={generating}>
                    <FileText className="h-4 w-4 mr-2" />
                    Generate First Report
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ) : (
          filteredReports.map((report) => (
            <Card key={report.id} className="hover:shadow-md transition-shadow">
              <CardContent className="py-6">
                <div className="space-y-4">
                  {/* Header */}
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        {getTypeIcon(report.type)}
                        <h3 className="text-lg font-semibold">{report.title}</h3>
                      </div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge className={`text-xs capitalize ${getTypeColor(report.type)}`}>
                          {report.type.replace('_', ' ')}
                        </Badge>
                        <Badge className={`text-xs ${getStatusColor(report.status)}`}>
                          {report.status}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {new Date(report.generated_at).toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Insights */}
                  <div className="bg-muted/50 rounded-lg p-4">
                    <p className="text-sm font-medium text-muted-foreground">AI Insights</p>
                    <p className="text-sm mt-2 line-clamp-2">{report.ai_insights}</p>
                  </div>

                  {/* Metrics */}
                  {report.metrics && Object.keys(report.metrics).length > 0 && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {Object.entries(report.metrics).slice(0, 4).map(([key, value]) => (
                        <div key={key} className="bg-muted/50 rounded-lg p-3">
                          <p className="text-xs font-medium text-muted-foreground capitalize">
                            {key.replace(/_/g, ' ')}
                          </p>
                          <p className="text-lg font-semibold mt-1">
                            {typeof value === 'number'
                              ? value.toFixed(value < 100 ? 1 : 0)
                              : value}
                            {typeof value === 'number' && (key.includes('rate') || key.includes('roi')) ? '%' : ''}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Summary */}
                  {report.summary && (
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Summary</p>
                      <p className="text-sm mt-1">{report.summary}</p>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex items-center justify-between pt-4 border-t">
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => report.docx_url ? window.open(report.docx_url, '_blank') : setError('Report file not available')}
                        disabled={!report.docx_url && !report.file_url}
                      >
                        <Eye className="h-4 w-4 mr-2" />
                        View Full
                      </Button>
                    </div>
                    <div className="flex gap-2">
                      {report.status === 'completed' && (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => downloadReport(report, 'pdf')}
                            disabled={!report.file_url}
                            title={report.file_url ? 'Download as PDF' : 'PDF not available'}
                          >
                            <File className="h-4 w-4 mr-2" />
                            PDF
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => downloadReport(report, 'docx')}
                            disabled={!report.docx_url}
                            title={report.docx_url ? 'Download as DOCX' : 'DOCX not available'}
                          >
                            <FileText className="h-4 w-4 mr-2" />
                            DOCX
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => downloadReport(report, 'json')}
                            title="Download report data as JSON"
                          >
                            <FileJson className="h-4 w-4 mr-2" />
                            JSON
                          </Button>
                        </>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteReport(report.id)}
                        className="text-destructive hover:text-destructive"
                        title="Delete report"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Performance Summary */}
      {reports.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Performance Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-muted/50 rounded-lg p-4">
                <p className="text-sm font-medium text-muted-foreground">Total Reports</p>
                <p className="text-2xl font-bold mt-2">{reports.length}</p>
              </div>
              <div className="bg-muted/50 rounded-lg p-4">
                <p className="text-sm font-medium text-muted-foreground">Completed</p>
                <p className="text-2xl font-bold mt-2">
                  {reports.filter((r) => r.status === 'completed').length}
                </p>
              </div>
              <div className="bg-muted/50 rounded-lg p-4">
                <p className="text-sm font-medium text-muted-foreground">Processing</p>
                <p className="text-2xl font-bold mt-2">
                  {reports.filter((r) => r.status === 'processing').length}
                </p>
              </div>
              <div className="bg-muted/50 rounded-lg p-4">
                <p className="text-sm font-medium text-muted-foreground">Avg P&L</p>
                <p className="text-2xl font-bold mt-2 text-green-600">
                  $
                  {(
                    reports.reduce((sum, r) => sum + (r.metrics?.profit_loss || 0), 0) /
                    reports.length
                  ).toFixed(0)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
