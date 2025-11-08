'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Clock, Play, RefreshCw } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import { getAgentConfig, getAgentIcon } from '@/lib/config/agents'

// Analysis Agents - Chart analysis and reporting
const analysisAgents = [
  { name: 'ChartWatcher', status: 'active', schedule: 'Every 6 hours', description: 'Pattern detection with OpenAI Vision' },
  { name: 'MorningPlanner', status: 'active', schedule: 'Daily at 08:25', description: 'Asia sweep & Y-Low setups' },
  { name: 'JournalBot', status: 'active', schedule: 'Daily at 21:00', description: 'AI-powered trading reports' },
]

// Trading Setup Agents - Entry/exit signals
const setupAgents = [
  { name: 'SignalBot', status: 'planned', schedule: 'Real-time', description: 'Entry/exit signals' },
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
      // Use Next.js API Route (works both locally and in production)
      const response = await fetch('/api/agents/trigger', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agent_name: backendAgentName,
          symbol: selectedSymbol === 'all' ? null : selectedSymbol,  // Pass symbol or null
          user_id: null,  // TODO: Get real UUID from Supabase session (for now: NULL = system-wide budget only)
          tier: 'free',  // Not used when user_id is NULL
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

  // Get agent card styling with border glow
  const getAgentCardClasses = (agentName: string, status: string) => {
    if (status === 'planned') return 'opacity-60'

    const agentConfig = getAgentConfig(agentName)
    if (!agentConfig) return ''

    // Map agent colors to Tailwind border and shadow classes
    const colorMap: Record<string, string> = {
      'blue': 'border-2 border-blue-500/50 shadow-lg shadow-blue-500/20 hover:border-blue-500 hover:shadow-blue-500/30 transition-all',
      'green': 'border-2 border-green-500/50 shadow-lg shadow-green-500/20 hover:border-green-500 hover:shadow-green-500/30 transition-all',
      'purple': 'border-2 border-purple-500/50 shadow-lg shadow-purple-500/20 hover:border-purple-500 hover:shadow-purple-500/30 transition-all',
      'orange': 'border-2 border-orange-500/50 shadow-lg shadow-orange-500/20 hover:border-orange-500 hover:shadow-orange-500/30 transition-all',
      'pink': 'border-2 border-pink-500/50 shadow-lg shadow-pink-500/20 hover:border-pink-500 hover:shadow-pink-500/30 transition-all',
    }

    return colorMap[agentConfig.color] || ''
  }

  // Helper function to render agent card
  const renderAgentCard = (agent: typeof analysisAgents[0]) => {
    const agentConfig = getAgentConfig(agent.name)

    return (
      <Card key={agent.name} className={getAgentCardClasses(agent.name, agent.status)}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-lg">{agentConfig?.icon || '🤖'}</span>
              <CardTitle className={`text-base ${agentConfig?.colors.text || ''}`}>{agent.name}</CardTitle>
            </div>
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
                onValueChange={(value: string) =>
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
    )
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
      <CardContent className="space-y-8">
        {/* Analysis Agents Section */}
        <div>
          <div className="flex items-center gap-3 mb-4 pb-2 border-b">
            <h3 className="text-xl font-bold">Analysis Agents</h3>
            <Badge variant="secondary" className="text-xs">{analysisAgents.length}</Badge>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {analysisAgents.map(renderAgentCard)}
          </div>
        </div>

        {/* Trading Setup Agents Section */}
        <div>
          <div className="flex items-center gap-3 mb-4 pb-2 border-b">
            <h3 className="text-xl font-bold">Trading Setups</h3>
            <Badge variant="secondary" className="text-xs">{setupAgents.length}</Badge>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {setupAgents.map(renderAgentCard)}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
