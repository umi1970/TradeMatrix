import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Bot, Activity, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react'

interface AgentStatus {
  name: string
  status: 'active' | 'idle' | 'error' | 'running'
  lastRun?: string
  description: string
  icon?: 'chart' | 'signal' | 'risk' | 'journal'
}

interface AgentStatusCardProps {
  agent: AgentStatus
  onAction?: () => void
}

export function AgentStatusCard({ agent, onAction }: AgentStatusCardProps) {
  const getStatusBadge = () => {
    switch (agent.status) {
      case 'active':
        return (
          <Badge variant="default" className="gap-1">
            <CheckCircle2 className="h-3 w-3" />
            Active
          </Badge>
        )
      case 'running':
        return (
          <Badge variant="secondary" className="gap-1">
            <Loader2 className="h-3 w-3 animate-spin" />
            Running
          </Badge>
        )
      case 'error':
        return (
          <Badge variant="destructive" className="gap-1">
            <AlertCircle className="h-3 w-3" />
            Error
          </Badge>
        )
      default:
        return (
          <Badge variant="outline" className="gap-1">
            <Activity className="h-3 w-3" />
            Idle
          </Badge>
        )
    }
  }

  const getAgentIcon = () => {
    switch (agent.icon) {
      case 'chart':
        return 'h-4 w-4 text-blue-600'
      case 'signal':
        return 'h-4 w-4 text-green-600'
      case 'risk':
        return 'h-4 w-4 text-orange-600'
      case 'journal':
        return 'h-4 w-4 text-purple-600'
      default:
        return 'h-4 w-4 text-gray-600'
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Bot className={getAgentIcon()} />
          {agent.name}
        </CardTitle>
        {getStatusBadge()}
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">{agent.description}</p>

          {agent.lastRun && (
            <div className="text-xs text-muted-foreground">
              Last run: {agent.lastRun}
            </div>
          )}

          {onAction && (
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              onClick={onAction}
              disabled={agent.status === 'running'}
            >
              {agent.status === 'running' ? 'Running...' : 'Run Agent'}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

// Default export for easy async loading
export default AgentStatusCard
