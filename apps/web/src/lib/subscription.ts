/**
 * Subscription Feature Gating Library
 * Controls access to features based on subscription tier
 */

export type SubscriptionTier = 'free' | 'starter' | 'pro' | 'expert'

/**
 * Feature definitions for each subscription tier
 */
export const FEATURES = {
  // Basic features
  BASIC_MARKET_OVERVIEW: 'basic_market_overview',
  LIMITED_REPORTS: 'limited_reports',

  // Starter tier
  DAILY_REPORTS: 'daily_reports',
  EMAIL_ALERTS: 'email_alerts',
  BASIC_CHARTS: 'basic_charts',

  // Pro tier
  BACKTESTING: 'backtesting',
  API_ACCESS: 'api_access',
  ADVANCED_CHARTS: 'advanced_charts',
  REAL_TIME_ALERTS: 'real_time_alerts',
  CUSTOM_INDICATORS: 'custom_indicators',
  EXPORT_DATA: 'export_data',

  // Expert tier
  CUSTOM_STRATEGIES: 'custom_strategies',
  PRIORITY_SUPPORT: 'priority_support',
  WHATSAPP_ALERTS: 'whatsapp_alerts',
  ADVANCED_AI_ANALYSIS: 'advanced_ai_analysis',
  UNLIMITED_BACKTESTS: 'unlimited_backtests',
  WHITE_LABEL: 'white_label',
} as const

export type Feature = typeof FEATURES[keyof typeof FEATURES]

/**
 * Feature access matrix
 * Defines which features are available at each tier
 */
const TIER_FEATURES: Record<SubscriptionTier, Feature[]> = {
  free: [
    FEATURES.BASIC_MARKET_OVERVIEW,
    FEATURES.LIMITED_REPORTS,
  ],
  starter: [
    FEATURES.BASIC_MARKET_OVERVIEW,
    FEATURES.LIMITED_REPORTS,
    FEATURES.DAILY_REPORTS,
    FEATURES.EMAIL_ALERTS,
    FEATURES.BASIC_CHARTS,
  ],
  pro: [
    FEATURES.BASIC_MARKET_OVERVIEW,
    FEATURES.LIMITED_REPORTS,
    FEATURES.DAILY_REPORTS,
    FEATURES.EMAIL_ALERTS,
    FEATURES.BASIC_CHARTS,
    FEATURES.BACKTESTING,
    FEATURES.API_ACCESS,
    FEATURES.ADVANCED_CHARTS,
    FEATURES.REAL_TIME_ALERTS,
    FEATURES.CUSTOM_INDICATORS,
    FEATURES.EXPORT_DATA,
  ],
  expert: [
    FEATURES.BASIC_MARKET_OVERVIEW,
    FEATURES.LIMITED_REPORTS,
    FEATURES.DAILY_REPORTS,
    FEATURES.EMAIL_ALERTS,
    FEATURES.BASIC_CHARTS,
    FEATURES.BACKTESTING,
    FEATURES.API_ACCESS,
    FEATURES.ADVANCED_CHARTS,
    FEATURES.REAL_TIME_ALERTS,
    FEATURES.CUSTOM_INDICATORS,
    FEATURES.EXPORT_DATA,
    FEATURES.CUSTOM_STRATEGIES,
    FEATURES.PRIORITY_SUPPORT,
    FEATURES.WHATSAPP_ALERTS,
    FEATURES.ADVANCED_AI_ANALYSIS,
    FEATURES.UNLIMITED_BACKTESTS,
    FEATURES.WHITE_LABEL,
  ],
}

/**
 * Resource limits per tier
 */
export const TIER_LIMITS = {
  free: {
    maxTrades: 10,
    maxReports: 5,
    maxBacktests: 0,
    maxAlerts: 0,
    apiCallsPerDay: 0,
  },
  starter: {
    maxTrades: 100,
    maxReports: 50,
    maxBacktests: 0,
    maxAlerts: 10,
    apiCallsPerDay: 0,
  },
  pro: {
    maxTrades: 1000,
    maxReports: 500,
    maxBacktests: 50,
    maxAlerts: 100,
    apiCallsPerDay: 1000,
  },
  expert: {
    maxTrades: -1, // unlimited
    maxReports: -1, // unlimited
    maxBacktests: -1, // unlimited
    maxAlerts: -1, // unlimited
    apiCallsPerDay: 10000,
  },
} as const

/**
 * Check if a tier has access to a specific feature
 */
export function canAccessFeature(tier: SubscriptionTier, feature: Feature): boolean {
  const tierFeatures = TIER_FEATURES[tier]
  return tierFeatures.includes(feature)
}

/**
 * Get all features available for a tier
 */
export function getTierFeatures(tier: SubscriptionTier): Feature[] {
  return TIER_FEATURES[tier]
}

/**
 * Get resource limits for a tier
 */
export function getTierLimits(tier: SubscriptionTier) {
  return TIER_LIMITS[tier]
}

/**
 * Check if a user has reached their limit for a resource
 */
export function hasReachedLimit(
  tier: SubscriptionTier,
  resource: keyof typeof TIER_LIMITS.free,
  currentCount: number
): boolean {
  const limit = TIER_LIMITS[tier][resource]

  // -1 means unlimited
  if (limit === -1) return false

  return currentCount >= limit
}

/**
 * Get the minimum tier required for a feature
 */
export function getMinimumTierForFeature(feature: Feature): SubscriptionTier {
  const tiers: SubscriptionTier[] = ['free', 'starter', 'pro', 'expert']

  for (const tier of tiers) {
    if (canAccessFeature(tier, feature)) {
      return tier
    }
  }

  return 'expert' // fallback to highest tier
}

/**
 * Tier pricing information
 */
export const TIER_PRICING = {
  free: {
    name: 'Free',
    price: 0,
    currency: 'EUR',
    interval: 'month',
    description: 'Perfect for getting started',
    features: [
      'Basic market overview',
      'Limited to 10 trades',
      '5 reports per month',
      'Community support',
    ],
    stripePriceId: null, // Free tier has no Stripe price
  },
  starter: {
    name: 'Starter',
    price: 9,
    currency: 'EUR',
    interval: 'month',
    description: 'For active traders',
    features: [
      'Daily AI reports',
      'Email alerts',
      'Up to 100 trades',
      '50 reports per month',
      'Basic charts',
      'Email support',
    ],
    stripePriceId: process.env.NEXT_PUBLIC_STRIPE_PRICE_STARTER, // Set in .env
  },
  pro: {
    name: 'Pro',
    price: 39,
    currency: 'EUR',
    interval: 'month',
    description: 'For professional traders',
    features: [
      'Everything in Starter',
      'Backtesting (50/month)',
      'API access (1000 calls/day)',
      'Advanced charts',
      'Real-time alerts',
      'Custom indicators',
      'Export data',
      'Priority email support',
    ],
    stripePriceId: process.env.NEXT_PUBLIC_STRIPE_PRICE_PRO, // Set in .env
  },
  expert: {
    name: 'Expert',
    price: 79,
    currency: 'EUR',
    interval: 'month',
    description: 'For trading firms & experts',
    features: [
      'Everything in Pro',
      'Unlimited trades & reports',
      'Unlimited backtests',
      'Custom strategies',
      'WhatsApp alerts',
      'Advanced AI analysis',
      'API access (10k calls/day)',
      'Priority support',
      'White-label option',
    ],
    stripePriceId: process.env.NEXT_PUBLIC_STRIPE_PRICE_EXPERT, // Set in .env
  },
} as const

/**
 * Get pricing information for a tier
 */
export function getTierPricing(tier: SubscriptionTier) {
  return TIER_PRICING[tier]
}

/**
 * Get all available tiers (excluding free for subscription selection)
 */
export function getSubscriptionTiers(): SubscriptionTier[] {
  return ['starter', 'pro', 'expert']
}

/**
 * Check if user can upgrade from current tier
 */
export function canUpgrade(currentTier: SubscriptionTier): boolean {
  const tierOrder: SubscriptionTier[] = ['free', 'starter', 'pro', 'expert']
  const currentIndex = tierOrder.indexOf(currentTier)
  return currentIndex < tierOrder.length - 1
}

/**
 * Get the next tier for upgrade
 */
export function getNextTier(currentTier: SubscriptionTier): SubscriptionTier | null {
  const tierOrder: SubscriptionTier[] = ['free', 'starter', 'pro', 'expert']
  const currentIndex = tierOrder.indexOf(currentTier)

  if (currentIndex < tierOrder.length - 1) {
    return tierOrder[currentIndex + 1]
  }

  return null
}
