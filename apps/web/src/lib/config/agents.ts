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
  | 'AI Setup Generator'
  | 'TradingView'

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
  'AI Setup Generator': {
    id: 'AI Setup Generator',
    name: 'AI Setup Generator',
    description: 'AI-Powered Trading Setup Generation',
    icon: '🤖',
    color: 'cyan',
    colors: {
      text: 'text-cyan-600 dark:text-cyan-400',
      bg: 'bg-cyan-600',
      bgLight: 'bg-cyan-50 dark:bg-cyan-950',
      border: 'border-cyan-500',
      ring: 'ring-cyan-500',
      badge: {
        bg: 'bg-cyan-100 dark:bg-cyan-900',
        text: 'text-cyan-700 dark:text-cyan-300',
      },
    },
    schedule: 'On-Demand',
  },
  TradingView: {
    id: 'TradingView',
    name: 'TradingView',
    description: 'TradingView Alert Automation with AI Analysis',
    icon: '📈',
    color: 'indigo',
    colors: {
      text: 'text-indigo-600 dark:text-indigo-400',
      bg: 'bg-indigo-600',
      bgLight: 'bg-indigo-50 dark:bg-indigo-950',
      border: 'border-indigo-500',
      ring: 'ring-indigo-500',
      badge: {
        bg: 'bg-indigo-100 dark:bg-indigo-900',
        text: 'text-indigo-700 dark:text-indigo-300',
      },
    },
    schedule: 'Real-time (Alert-based)',
  },
}

/**
 * Get all available agents
 */
export function getAgents(): AgentConfig[] {
  return Object.values(AGENT_CONFIGS)
}

/**
 * Normalize agent name from snake_case to PascalCase
 */
function normalizeAgentName(name: string): string {
  // Trim whitespace
  const trimmed = name.trim()

  // If already PascalCase, return as is
  if (trimmed in AGENT_CONFIGS) return trimmed

  // Convert snake_case to PascalCase (e.g., "chart_watcher" -> "ChartWatcher")
  const normalized = trimmed
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join('')

  return normalized
}

/**
 * Get agent config by ID (supports both PascalCase and snake_case)
 */
export function getAgentConfig(agentId: string): AgentConfig | undefined {
  const normalizedId = normalizeAgentName(agentId)
  return AGENT_CONFIGS[normalizedId as AgentId]
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
 * NOTE: Using switch instead of config object to ensure Tailwind CSS includes all classes
 */
export function getAgentColor(agentId: string, context: 'text' | 'bg' | 'bgLight' | 'border' | 'ring' = 'text'): string {
  const config = getAgentConfig(agentId)
  if (!config) return 'text-gray-500'

  // For 'text' context, use switch statement to ensure Tailwind includes classes
  if (context === 'text') {
    switch (config.color) {
      case 'blue':
        return 'text-blue-600 dark:text-blue-400'
      case 'green':
        return 'text-green-600 dark:text-green-400'
      case 'purple':
        return 'text-purple-600 dark:text-purple-400'
      case 'orange':
        return 'text-orange-600 dark:text-orange-400'
      case 'pink':
        return 'text-pink-600 dark:text-pink-400'
      case 'cyan':
        return 'text-cyan-600 dark:text-cyan-400'
      case 'indigo':
        return 'text-indigo-600 dark:text-indigo-400'
      default:
        return 'text-gray-500'
    }
  }

  // For other contexts, return from config (less commonly used)
  return config.colors[context]
}

/**
 * Get agent badge color classes
 * NOTE: Using switch instead of config object to ensure Tailwind CSS includes all classes
 */
export function getAgentBadgeColors(agentId: string): { bg: string; text: string } {
  const config = getAgentConfig(agentId)
  if (!config) {
    return {
      bg: 'bg-gray-100 dark:bg-gray-800',
      text: 'text-gray-700 dark:text-gray-300',
    }
  }

  // Direct switch statement ensures Tailwind CSS purging includes all classes
  switch (config.color) {
    case 'blue':
      return {
        bg: 'bg-blue-100 dark:bg-blue-900',
        text: 'text-blue-700 dark:text-blue-300',
      }
    case 'green':
      return {
        bg: 'bg-green-100 dark:bg-green-900',
        text: 'text-green-700 dark:text-green-300',
      }
    case 'purple':
      return {
        bg: 'bg-purple-100 dark:bg-purple-900',
        text: 'text-purple-700 dark:text-purple-300',
      }
    case 'orange':
      return {
        bg: 'bg-orange-100 dark:bg-orange-900',
        text: 'text-orange-700 dark:text-orange-300',
      }
    case 'pink':
      return {
        bg: 'bg-pink-100 dark:bg-pink-900',
        text: 'text-pink-700 dark:text-pink-300',
      }
    case 'cyan':
      return {
        bg: 'bg-cyan-100 dark:bg-cyan-900',
        text: 'text-cyan-700 dark:text-cyan-300',
      }
    case 'indigo':
      return {
        bg: 'bg-indigo-100 dark:bg-indigo-900',
        text: 'text-indigo-700 dark:text-indigo-300',
      }
    default:
      return {
        bg: 'bg-gray-100 dark:bg-gray-800',
        text: 'text-gray-700 dark:text-gray-300',
      }
  }
}

/**
 * Get agent left border class for cards
 * NOTE: Using switch instead of Record to ensure Tailwind CSS includes all classes
 */
export function getAgentLeftBorderClass(agentId: string): string {
  const config = getAgentConfig(agentId)
  if (!config) return 'border-l-4 border-l-gray-500'

  // Direct switch statement ensures Tailwind CSS purging includes all classes
  switch (config.color) {
    case 'blue':
      return 'border-l-4 border-l-blue-500'
    case 'green':
      return 'border-l-4 border-l-green-500'
    case 'purple':
      return 'border-l-4 border-l-purple-500'
    case 'orange':
      return 'border-l-4 border-l-orange-500'
    case 'pink':
      return 'border-l-4 border-l-pink-500'
    case 'cyan':
      return 'border-l-4 border-l-cyan-500'
    case 'indigo':
      return 'border-l-4 border-l-indigo-500'
    default:
      return 'border-l-4 border-l-gray-500'
  }
}
