/**
 * BillingPortal Component
 * Button to open Stripe Billing Portal for subscription management
 */

'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { CreditCard, Loader2 } from 'lucide-react'

interface BillingPortalProps {
  variant?: 'default' | 'outline' | 'ghost'
  size?: 'default' | 'sm' | 'lg'
  className?: string
  children?: React.ReactNode
}

export function BillingPortal({
  variant = 'outline',
  size = 'default',
  className,
  children,
}: BillingPortalProps) {
  const [isLoading, setIsLoading] = useState(false)

  const handleOpenPortal = async () => {
    setIsLoading(true)

    try {
      // Call API to create billing portal session
      const response = await fetch('/api/stripe/portal', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error('Failed to create billing portal session')
      }

      const { url } = await response.json()

      // Redirect to billing portal
      if (url) {
        window.location.href = url
      }
    } catch (error) {
      console.error('Error opening billing portal:', error)
      alert('Failed to open billing portal. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Button
      variant={variant}
      size={size}
      className={className}
      onClick={handleOpenPortal}
      disabled={isLoading}
    >
      {isLoading ? (
        <>
          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          Loading...
        </>
      ) : (
        <>
          <CreditCard className="h-4 w-4 mr-2" />
          {children || 'Manage Subscription'}
        </>
      )}
    </Button>
  )
}
