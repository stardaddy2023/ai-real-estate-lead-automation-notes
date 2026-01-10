"use client"

import * as React from "react"
import { useAppStore } from "@/lib/store"
import MarketRecon from "@/components/scout/MarketRecon"
import LeadScout from "@/components/scout/LeadScout"
import { LeadInbox } from "@/components/leads/lead-inbox"
import { DispositionsDashboard } from "@/components/dispositions/DispositionsDashboard"
import { AnalyticsView } from "@/components/dashboard/AnalyticsView"
import { RecorderDocuments } from "@/components/recorder/RecorderDocuments"

export default function DashboardPage() {
    const { activeZone } = useAppStore()
    const zone = activeZone as string;

    switch (zone) {
        case 'market_scout':
            return <MarketRecon />
        case 'leads':
            return <LeadScout />
        case 'my_leads':
            return (
                <div className="p-8 h-full overflow-y-auto">
                    <LeadInbox />
                </div>
            )
        case 'recorder':
            return <RecorderDocuments />
        case 'crm':
            return <DispositionsDashboard />
        case 'analytics':
            return <AnalyticsView />
        default:
            return <AnalyticsView />
    }
}
