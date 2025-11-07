'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Clock, Play } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

const agents = [
  { name: 'ChartWatcher', status: 'active', schedule: 'Every 6 hours', description: 'Pattern detection with OpenAI Vision' },
  { name: 'MorningPlanner', status: 'active', schedule: 'Daily at 08:25', description: 'Asia sweep & Y-Low setups' },
  { name: 'SignalBot', status: 'planned', schedule: 'Real-time', description: 'Entry/exit signals' },
  { name: 'JournalBot', status: 'active', schedule: 'Daily at 21:00', description: 'AI-powered trading reports' },
  { name: 'USOpenPlanner', status: 'planned', schedule: 'Daily at 15:30', description: 'US opening range breakouts' },
]

export function AgentControlPanel() {
  const { toast } = useToast()
  const [triggeringAgent, setTriggeringAgent] = useState<string | null>(null)

  const triggerAgent = async (agentName: string) => {
    setTriggeringAgent(agentName)

    // Convert agent name to backend format
    // "ChartWatcher" -> "chart_watcher"
    const backendAgentName = agentName
      .replace(/([A-Z])/g, '_$1')
      .toLowerCase()
      .replace(/^_/, '')

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/agents/trigger`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agent_name: backendAgentName,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to trigger agent')
      }

      const data = await response.json()

      toast({
        title: "Agent Started",
        description: `${agentName} is now running. Results will appear below.`,
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to start agent. Please try again.",
        variant: "destructive",
      })
    } finally {
      setTriggeringAgent(null)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>AI Agent Controls</CardTitle>
        <CardDescription>
          Manage and monitor your AI trading agents
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {agents.map((agent) => (
            <Card key={agent.name} className={agent.status === 'planned' ? 'opacity-60' : ''}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">{agent.name}</CardTitle>
                  <Badge variant={agent.status === 'active' ? 'default' : 'secondary'}>
                    {agent.status}
                  </Badge>
                </div>
                <CardDescription className="text-xs">
                  {agent.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="pb-3">
                <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
                  <Clock className="h-3 w-3" />
                  <span>{agent.schedule}</span>
                </div>
                {agent.status === 'active' && (
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full"
                    onClick={() => triggerAgent(agent.name)}
                    disabled={triggeringAgent === agent.name}
                  >
                    <Play className="h-3 w-3 mr-1" />
                    {triggeringAgent === agent.name ? 'Starting...' : 'Run Now'}
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
