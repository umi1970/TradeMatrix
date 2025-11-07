'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Clock, Play, RefreshCw } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

const agents = [
  { name: 'ChartWatcher', status: 'active', schedule: 'Every 6 hours', description: 'Pattern detection with OpenAI Vision' },
  { name: 'MorningPlanner', status: 'active', schedule: 'Daily at 08:25', description: 'Asia sweep & Y-Low setups' },
  { name: 'SignalBot', status: 'planned', schedule: 'Real-time', description: 'Entry/exit signals' },
  { name: 'JournalBot', status: 'active', schedule: 'Daily at 21:00', description: 'AI-powered trading reports' },
  { name: 'USOpenPlanner', status: 'planned', schedule: 'Daily at 15:30', description: 'US opening range breakouts' },
]

const symbols = [
  { value: 'all', label: 'All Symbols' },
  { value: 'DAX', label: 'DAX' },
  { value: 'NDX', label: 'NASDAQ 100' },
  { value: 'DJI', label: 'Dow Jones' },
  { value: 'EUR/USD', label: 'EUR/USD' },
  { value: 'EUR/GBP', label: 'EUR/GBP' },
]

export function AgentControlPanel() {
  const { toast } = useToast()
  const router = useRouter()
  const [triggeringAgent, setTriggeringAgent] = useState<string | null>(null)
  const [refreshCountdown, setRefreshCountdown] = useState<number | null>(null)
  const [selectedSymbols, setSelectedSymbols] = useState<Record<string, string>>({
    ChartWatcher: 'all',
    MorningPlanner: 'all',
    JournalBot: 'all',
  })

  // Auto-refresh countdown effect
  useEffect(() => {
    if (refreshCountdown === null || refreshCountdown <= 0) return

    const timer = setInterval(() => {
      setRefreshCountdown((prev) => {
        if (prev === null || prev <= 1) {
          // Refresh page when countdown reaches 0
          router.refresh()
          return null
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [refreshCountdown, router])

  const triggerAgent = async (agentName: string) => {
    setTriggeringAgent(agentName)

    // Convert agent name to backend format
    // "ChartWatcher" -> "chart_watcher"
    const backendAgentName = agentName
      .replace(/([A-Z])/g, '_$1')
      .toLowerCase()
      .replace(/^_/, '')

    // Get selected symbol for this agent
    const selectedSymbol = selectedSymbols[agentName] || 'all'

    try {
      // Use Netlify Function as proxy to avoid HTTPS->HTTP mixed content issues
      const response = await fetch('/.netlify/functions/trigger-agent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agent_name: backendAgentName,
          symbol: selectedSymbol === 'all' ? null : selectedSymbol,  // Pass symbol or null
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to trigger agent')
      }

      const data = await response.json()

      const symbolText = selectedSymbol === 'all' ? 'all symbols' : selectedSymbol

      toast({
        title: "Agent Started",
        description: `${agentName} is analyzing ${symbolText}. Page will auto-refresh in 60 seconds.`,
      })

      // Start auto-refresh countdown (60 seconds)
      setRefreshCountdown(60)
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
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>AI Agent Controls</CardTitle>
            <CardDescription>
              Manage and monitor your AI trading agents
            </CardDescription>
          </div>
          {refreshCountdown !== null && refreshCountdown > 0 && (
            <Badge variant="secondary" className="flex items-center gap-2">
              <RefreshCw className="h-3 w-3 animate-spin" />
              Auto-refresh in {refreshCountdown}s
            </Badge>
          )}
        </div>
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
                  <div className="space-y-2">
                    <Select
                      value={selectedSymbols[agent.name] || 'all'}
                      onValueChange={(value) =>
                        setSelectedSymbols((prev) => ({ ...prev, [agent.name]: value }))
                      }
                    >
                      <SelectTrigger className="w-full h-8 text-xs">
                        <SelectValue placeholder="Select symbol" />
                      </SelectTrigger>
                      <SelectContent>
                        {symbols.map((symbol) => (
                          <SelectItem key={symbol.value} value={symbol.value} className="text-xs">
                            {symbol.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
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
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
