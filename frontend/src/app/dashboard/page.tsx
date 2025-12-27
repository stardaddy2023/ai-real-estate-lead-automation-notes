"use client"

import * as React from "react"
import { useAppStore } from "@/lib/store"
import { MarketScout } from "@/components/scout/MarketScout"
import LeadScout from "@/components/scout/LeadScout"
import { LeadInbox } from "@/components/leads/lead-inbox"
import { DispositionsDashboard } from "@/components/dispositions/DispositionsDashboard"
import { AnalyticsView } from "@/components/dashboard/AnalyticsView"

export default function DashboardPage() {
    const { activeZone } = useAppStore()

    switch (activeZone) {
        case 'market_scout':
            return <MarketScout />
        case 'leads':
            return <LeadScout />
        case 'my_leads':
            return (
                <div className="p-8 h-full overflow-y-auto">
                    <LeadInbox />
                </div>
            )
        case 'crm':
            return <DispositionsDashboard />
        case 'analytics':
            return <AnalyticsView />
        default:
            return <AnalyticsView />
    }
}
