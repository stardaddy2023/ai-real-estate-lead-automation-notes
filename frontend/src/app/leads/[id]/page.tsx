import { notFound } from "next/navigation"
import { DealHeader } from "@/components/deals/deal-header"
import { DealMetrics } from "@/components/deals/deal-metrics"
import { DealPhotos } from "@/components/deals/deal-photos"
import { Lead } from "@/types"

async function getLead(id: string): Promise<Lead | null> {
    try {
        const res = await fetch(`http://127.0.0.1:8000/api/v1/leads/${id}`, {
            cache: "no-store",
        })
        if (!res.ok) return null
        return res.json()
    } catch (error) {
        console.error("Failed to fetch lead:", error)
        return null
    }
}

export default async function LeadPage({
    params,
}: {
    params: Promise<{ id: string }>
}) {
    const { id } = await params
    const lead = await getLead(id)

    if (!lead) {
        notFound()
    }

    return (
        <div className="container mx-auto py-10 space-y-8">
            <DealHeader lead={lead} />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-2 space-y-6">
                    <DealMetrics leadId={lead.id} />
                </div>
                <div>
                    <DealPhotos />
                </div>
            </div>
        </div>
    )
}
