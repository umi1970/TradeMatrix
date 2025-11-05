'use client'

import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { TrashIcon, ExternalLinkIcon } from 'lucide-react'
import { createBrowserClient } from '@/lib/supabase/client'
import { useToast } from '@/hooks/use-toast'

interface ChartSnapshotCardProps {
  snapshot: {
    id: string
    chart_url: string
    timeframe: string
    created_by_agent: string
    created_at: string
    symbol?: {
      symbol: string
      name: string
    }
  }
  onDelete: () => void
}

export function ChartSnapshotCard({ snapshot, onDelete }: ChartSnapshotCardProps) {
  const supabase = createBrowserClient()
  const { toast } = useToast()

  const handleDelete = async () => {
    if (!confirm('Delete this chart snapshot?')) return

    try {
      const { error } = await supabase
        .from('chart_snapshots')
        .delete()
        .eq('id', snapshot.id)

      if (error) throw error

      toast({
        title: 'Success',
        description: 'Chart snapshot deleted successfully',
      })
      onDelete()
    } catch (error) {
      console.error('Error deleting snapshot:', error)
      toast({
        title: 'Error',
        description: 'Failed to delete snapshot',
        variant: 'destructive',
      })
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'just now'
    if (diffMins < 60) return `${diffMins} min ago`
    if (diffHours < 24) return `${diffHours}h ago`
    return `${diffDays}d ago`
  }

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">
              {snapshot.symbol?.name || 'Unknown'}
            </CardTitle>
            <p className="text-xs text-muted-foreground">
              {snapshot.symbol?.symbol || 'N/A'}
            </p>
          </div>
          <Badge variant="secondary">{snapshot.timeframe}</Badge>
        </div>
      </CardHeader>
      <CardContent className="pb-3">
        <div className="aspect-video bg-muted rounded-md overflow-hidden">
          <img
            src={snapshot.chart_url}
            alt={`Chart for ${snapshot.symbol?.symbol}`}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).src =
                'https://via.placeholder.com/400x300?text=Chart+Unavailable'
            }}
          />
        </div>
      </CardContent>
      <CardFooter className="flex items-center justify-between">
        <div className="text-xs text-muted-foreground">
          <div>{snapshot.created_by_agent}</div>
          <div>{formatDate(snapshot.created_at)}</div>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" asChild>
            <a href={snapshot.chart_url} target="_blank" rel="noopener noreferrer">
              <ExternalLinkIcon className="h-4 w-4" />
            </a>
          </Button>
          <Button variant="ghost" size="sm" onClick={handleDelete}>
            <TrashIcon className="h-4 w-4" />
          </Button>
        </div>
      </CardFooter>
    </Card>
  )
}
