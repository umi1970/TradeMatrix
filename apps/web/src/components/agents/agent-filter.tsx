'use client'

import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/button'
import { Bot, FilterX } from 'lucide-react'
import { getAgents } from '@/lib/config/agents'

const AVAILABLE_AGENTS = getAgents()

interface AgentFilterProps {
  currentFilter?: string[]
}

export function AgentFilter({ currentFilter = [] }: AgentFilterProps) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [selectedAgents, setSelectedAgents] = useState<string[]>(currentFilter)

  const handleToggleAgent = (agentId: string) => {
    setSelectedAgents((prev) => {
      if (prev.includes(agentId)) {
        return prev.filter((id) => id !== agentId)
      } else {
        return [...prev, agentId]
      }
    })
  }

  const handleApplyFilter = () => {
    const params = new URLSearchParams(searchParams.toString())

    if (selectedAgents.length > 0) {
      params.set('agents', selectedAgents.join(','))
    } else {
      params.delete('agents')
    }

    router.push(`/agents?${params.toString()}`)
  }

  const handleClearFilter = () => {
    setSelectedAgents([])
    router.push('/agents')
  }

  const isFilterActive = selectedAgents.length > 0

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <Bot className="h-4 w-4" />
            Filter by Agent
          </CardTitle>
          {isFilterActive && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearFilter}
              className="h-8 gap-2"
            >
              <FilterX className="h-4 w-4" />
              Clear
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {/* Agent Checkboxes */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {AVAILABLE_AGENTS.map((agent) => {
              const isSelected = selectedAgents.includes(agent.id)
              return (
                <div
                  key={agent.id}
                  className="flex items-start space-x-3 p-3 rounded-lg border hover:bg-muted/50 transition-colors cursor-pointer"
                  onClick={() => handleToggleAgent(agent.id)}
                >
                  <Checkbox
                    id={agent.id}
                    checked={isSelected}
                    onCheckedChange={() => handleToggleAgent(agent.id)}
                    onClick={(e: React.MouseEvent) => e.stopPropagation()}
                  />
                  <div className="flex-1 space-y-1">
                    <label
                      htmlFor={agent.id}
                      className={`text-sm font-medium leading-none cursor-pointer flex items-center gap-1.5 ${agent.colors.text}`}
                    >
                      <span>{agent.icon}</span>
                      <span>{agent.name}</span>
                    </label>
                    <p className="text-xs text-muted-foreground">
                      {agent.description}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Apply Filter Button */}
          <div className="flex items-center justify-between pt-2">
            <p className="text-xs text-muted-foreground">
              {selectedAgents.length === 0
                ? 'Select agents to filter setups'
                : `${selectedAgents.length} agent${selectedAgents.length === 1 ? '' : 's'} selected`}
            </p>
            <Button
              size="sm"
              onClick={handleApplyFilter}
              disabled={
                JSON.stringify(selectedAgents.sort()) ===
                JSON.stringify(currentFilter.sort())
              }
            >
              Apply Filter
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
