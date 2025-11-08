/**
 * Global AI Agent Configuration
 *
 * Centralized agent metadata including colors, icons, descriptions.
 * Use this config everywhere (filters, badges, reports, setups, charts)
 */

export type AgentId =
  | 'ChartWatcher'
  | 'SignalBot'
  | 'MorningPlanner'
  | 'JournalBot'
  | 'USOpenPlanner'

export interface AgentConfig {
  id: AgentId
  name: string
  description: string
  /** Base color name (e.g., 'blue', 'green') */
  color: string
  /** Tailwind color classes for different contexts */
  colors: {
    text: string      // e.g., 'text-blue-500'
    bg: string        // e.g., 'bg-blue-500'
    bgLight: string   // e.g., 'bg-blue-50 dark:bg-blue-950'
    border: string    // e.g., 'border-blue-500'
    ring: string      // e.g., 'ring-blue-500'
    badge: {
      bg: string      // e.g., 'bg-blue-100 dark:bg-blue-900'
      text: string    // e.g., 'text-blue-700 dark:text-blue-300'
    }
  }
  /** Emoji icon */
  icon: string
  /** When this agent runs (cron description) */
  schedule?: string
}

export const AGENT_CONFIGS: Record<AgentId, AgentConfig> = {
  ChartWatcher: {
    id: 'ChartWatcher',
    name: 'ChartWatcher',
    description: 'Pattern Detection & Technical Analysis',
    icon: '📊',
    color: 'blue',
    colors: {
      text: 'text-blue-600 dark:text-blue-400',
      bg: 'bg-blue-600',
      bgLight: 'bg-blue-50 dark:bg-blue-950',
      border: 'border-blue-500',
      ring: 'ring-blue-500',
      badge: {
        bg: 'bg-blue-100 dark:bg-blue-900',
        text: 'text-blue-700 dark:text-blue-300',
      },
    },
    schedule: 'Every 6 hours (Mon-Fri)',
  },
  SignalBot: {
    id: 'SignalBot',
    name: 'SignalBot',
    description: 'Entry & Exit Signal Generator',
    icon: '🎯',
    color: 'green',
    colors: {
      text: 'text-green-600 dark:text-green-400',
      bg: 'bg-green-600',
      bgLight: 'bg-green-50 dark:bg-green-950',
      border: 'border-green-500',
      ring: 'ring-green-500',
      badge: {
        bg: 'bg-green-100 dark:bg-green-900',
        text: 'text-green-700 dark:text-green-300',
      },
    },
    schedule: 'Real-time (Mon-Fri)',
  },
  MorningPlanner: {
    id: 'MorningPlanner',
    name: 'MorningPlanner',
    description: 'Daily Market Setup & Strategy',
    icon: '🌅',
    color: 'purple',
    colors: {
      text: 'text-purple-600 dark:text-purple-400',
      bg: 'bg-purple-600',
      bgLight: 'bg-purple-50 dark:bg-purple-950',
      border: 'border-purple-500',
      ring: 'ring-purple-500',
      badge: {
        bg: 'bg-purple-100 dark:bg-purple-900',
        text: 'text-purple-700 dark:text-purple-300',
      },
    },
    schedule: 'Daily at 08:25 MEZ (Mon-Fri)',
  },
  JournalBot: {
    id: 'JournalBot',
    name: 'JournalBot',
    description: 'Trade Review & Performance Analysis',
    icon: '📓',
    color: 'orange',
    colors: {
      text: 'text-orange-600 dark:text-orange-400',
      bg: 'bg-orange-600',
      bgLight: 'bg-orange-50 dark:bg-orange-950',
      border: 'border-orange-500',
      ring: 'ring-orange-500',
      badge: {
        bg: 'bg-orange-100 dark:bg-orange-900',
        text: 'text-orange-700 dark:text-orange-300',
      },
    },
    schedule: 'Daily at 21:00 MEZ (Mon-Fri)',
  },
  USOpenPlanner: {
    id: 'USOpenPlanner',
    name: 'US Open Planner',
    description: 'US Market Opening Strategy',
    icon: '🇺🇸',
    color: 'pink',
    colors: {
      text: 'text-pink-600 dark:text-pink-400',
      bg: 'bg-pink-600',
      bgLight: 'bg-pink-50 dark:bg-pink-950',
      border: 'border-pink-500',
      ring: 'ring-pink-500',
      badge: {
        bg: 'bg-pink-100 dark:bg-pink-900',
        text: 'text-pink-700 dark:text-pink-300',
      },
    },
    schedule: 'Daily at 15:25 MEZ (Mon-Fri)',
  },
}

/**
 * Get all available agents
 */
export function getAgents(): AgentConfig[] {
  return Object.values(AGENT_CONFIGS)
}

/**
 * Get agent config by ID
 */
export function getAgentConfig(agentId: string): AgentConfig | undefined {
  return AGENT_CONFIGS[agentId as AgentId]
}

/**
 * Get agent display name
 */
export function getAgentName(agentId: string): string {
  return getAgentConfig(agentId)?.name ?? agentId
}

/**
 * Get agent icon
 */
export function getAgentIcon(agentId: string): string {
  return getAgentConfig(agentId)?.icon ?? '🤖'
}

/**
 * Get agent color classes for specific context
 */
export function getAgentColor(agentId: string, context: 'text' | 'bg' | 'bgLight' | 'border' | 'ring' = 'text'): string {
  const config = getAgentConfig(agentId)
  if (!config) return 'text-gray-500'
  return config.colors[context]
}

/**
 * Get agent badge color classes
 */
export function getAgentBadgeColors(agentId: string): { bg: string; text: string } {
  const config = getAgentConfig(agentId)
  if (!config) {
    return {
      bg: 'bg-gray-100 dark:bg-gray-800',
      text: 'text-gray-700 dark:text-gray-300',
    }
  }
  return config.colors.badge
}
