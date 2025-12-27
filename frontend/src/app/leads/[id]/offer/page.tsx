import { notFound } from "next/navigation"
import { OfferForm } from "@/components/offers/offer-form"
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

export default async function OfferPage({
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
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Generate Offer</h1>
                    <p className="text-muted-foreground">Create and send a purchase agreement for {lead.address_street}</p>
                </div>
            </div>

            <OfferForm lead={lead} />
        </div>
    )
}
