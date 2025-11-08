'use client'

import { useState } from 'react'
import Image from 'next/image'
import { Trash2, ExternalLink, Filter, X } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { useChartSnapshots, useDeleteChartSnapshot } from '@/hooks/useChartSnapshots'
import type { ChartSnapshot } from '@/types/chart'
import { cn } from '@/lib/utils'

interface ChartSnapshotsGalleryProps {
  symbolId?: string
  limit?: number
  className?: string
}

export function ChartSnapshotsGallery({
  symbolId,
  limit = 10,
  className,
}: ChartSnapshotsGalleryProps) {
  const { data: snapshots = [], isLoading } = useChartSnapshots(symbolId)
  const deleteSnapshot = useDeleteChartSnapshot()

  const [selectedSnapshot, setSelectedSnapshot] = useState<ChartSnapshot | null>(null)
  const [deleteDialogSnapshot, setDeleteDialogSnapshot] = useState<ChartSnapshot | null>(null)
  const [timeframeFilter, setTimeframeFilter] = useState<string>('all')

  // Get unique timeframes for filter
  const uniqueTimeframes = Array.from(
    new Set(snapshots.map(s => s.timeframe))
  ).sort()

  // Filter and limit snapshots
  const filteredSnapshots = snapshots
    .filter(s => timeframeFilter === 'all' || s.timeframe === timeframeFilter)
    .slice(0, limit)

  const handleDelete = async () => {
    if (deleteDialogSnapshot) {
      await deleteSnapshot.mutateAsync(deleteDialogSnapshot.id)
      setDeleteDialogSnapshot(null)
      if (selectedSnapshot?.id === deleteDialogSnapshot.id) {
        setSelectedSnapshot(null)
      }
    }
  }

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Chart Snapshots</CardTitle>
          <CardDescription>Recent chart generations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="aspect-video" />
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (snapshots.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Chart Snapshots</CardTitle>
          <CardDescription>Recent chart generations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <p>No chart snapshots available</p>
            <p className="text-sm mt-2">Generate a chart to see it here</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Chart Snapshots</CardTitle>
              <CardDescription>
                {filteredSnapshots.length} of {snapshots.length} snapshots
              </CardDescription>
            </div>

            {/* Timeframe Filter */}
            {uniqueTimeframes.length > 1 && (
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-muted-foreground" />
                <Select value={timeframeFilter} onValueChange={setTimeframeFilter}>
                  <SelectTrigger className="w-[120px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    {uniqueTimeframes.map((tf) => (
                      <SelectItem key={tf} value={tf}>
                        {tf}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {filteredSnapshots.map((snapshot) => (
              <div
                key={snapshot.id}
                className="group relative aspect-video overflow-hidden rounded-lg border bg-muted cursor-pointer hover:ring-2 hover:ring-primary transition-all"
                onClick={() => setSelectedSnapshot(snapshot)}
              >
                <Image
                  src={snapshot.chart_url}
                  alt={`Chart ${snapshot.timeframe}`}
                  fill
                  className="object-cover"
                  unoptimized
                />

                {/* Overlay */}
                <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-2">
                  <Badge variant="secondary">{snapshot.timeframe}</Badge>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={(e) => {
                        e.stopPropagation()
                        window.open(snapshot.chart_url, '_blank')
                      }}
                    >
                      <ExternalLink className="h-3 w-3" />
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={(e) => {
                        e.stopPropagation()
                        setDeleteDialogSnapshot(snapshot)
                      }}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>

                {/* Timeframe Badge */}
                <div className="absolute top-2 right-2">
                  <Badge variant="secondary" className="text-xs">
                    {snapshot.timeframe}
                  </Badge>
                </div>

                {/* Trigger Type Badge */}
                <div className="absolute bottom-2 left-2">
                  <Badge
                    variant="outline"
                    className={cn(
                      'text-xs capitalize',
                      snapshot.trigger_type === 'alert' && 'bg-red-500/10 border-red-500',
                      snapshot.trigger_type === 'scheduled' && 'bg-blue-500/10 border-blue-500',
                      snapshot.trigger_type === 'manual' && 'bg-green-500/10 border-green-500'
                    )}
                  >
                    {snapshot.trigger_type}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Fullscreen Dialog */}
      <Dialog
        open={!!selectedSnapshot}
        onOpenChange={(open: boolean) => !open && setSelectedSnapshot(null)}
      >
        <DialogContent className="max-w-6xl">
          <DialogHeader>
            <DialogTitle>
              {selectedSnapshot?.symbol?.alias || selectedSnapshot?.symbol?.symbol || 'Chart'} - {selectedSnapshot?.timeframe}
            </DialogTitle>
            <DialogDescription>
              Generated {selectedSnapshot && new Date(selectedSnapshot.generated_at).toLocaleString()}
            </DialogDescription>
          </DialogHeader>

          {selectedSnapshot && (
            <div className="space-y-4">
              <div className="relative aspect-video w-full overflow-hidden rounded-lg border">
                <Image
                  src={selectedSnapshot.chart_url}
                  alt={`Chart ${selectedSnapshot.timeframe}`}
                  fill
                  className="object-contain"
                  unoptimized
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="flex gap-2">
                  <Badge variant="secondary">{selectedSnapshot.timeframe}</Badge>
                  <Badge
                    variant="outline"
                    className={cn(
                      'capitalize',
                      selectedSnapshot.trigger_type === 'alert' && 'bg-red-500/10 border-red-500',
                      selectedSnapshot.trigger_type === 'scheduled' && 'bg-blue-500/10 border-blue-500',
                      selectedSnapshot.trigger_type === 'manual' && 'bg-green-500/10 border-green-500'
                    )}
                  >
                    {selectedSnapshot.trigger_type}
                  </Badge>
                </div>

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => window.open(selectedSnapshot.chart_url, '_blank')}
                  >
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Open in New Tab
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={() => {
                      setDeleteDialogSnapshot(selectedSnapshot)
                      setSelectedSnapshot(null)
                    }}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </Button>
                </div>
              </div>

              <div className="text-sm text-muted-foreground space-y-1">
                <p>Generated: {new Date(selectedSnapshot.generated_at).toLocaleString()}</p>
                <p>Expires: {new Date(selectedSnapshot.expires_at).toLocaleString()}</p>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog
        open={!!deleteDialogSnapshot}
        onOpenChange={(open: boolean) => !open && setDeleteDialogSnapshot(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Chart Snapshot?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the chart snapshot.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
