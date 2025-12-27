"use client"

import { useEffect, useState } from "react"
import { InventoryCard } from "@/components/dispositions/inventory-card"
import { BuyerCard } from "@/components/dispositions/buyer-card"
import { Lead } from "@/types"

const MOCK_BUYERS = [
    { name: "Opendoor", score: 95, criteria: ["Single Family", "Phoenix", "Turnkey"] },
    { name: "Blackstone Group", score: 88, criteria: ["Portfolio", "Distressed", "Cash"] },
    { name: "Local Flipper LLC", score: 75, criteria: ["Fixer Upper", "Cheap", "Quick Close"] },
    { name: "Rental King", score: 60, criteria: ["Multi-family", "High Yield"] },
]

export function DispositionsDashboard() {
    const [inventory, setInventory] = useState<Lead[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        async function fetchInventory() {
            try {
                const res = await fetch("http://127.0.0.1:8000/api/v1/leads")
                if (res.ok) {
                    const leads: Lead[] = await res.json()
                    // For demo purposes, just take the first 3 leads as "Inventory"
                    setInventory(leads.slice(0, 3))
                }
            } catch (error) {
                console.error("Failed to fetch inventory:", error)
            } finally {
                setLoading(false)
            }
        }
        fetchInventory()
    }, [])

    return (
        <div className="p-8 space-y-8 h-full overflow-y-auto">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Dispositions</h1>
                <p className="text-muted-foreground">Manage your inventory and find buyers.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Left Column: Inventory */}
                <div className="space-y-6">
                    <h2 className="text-xl font-semibold">Ready for Sale ({inventory.length})</h2>
                    <div className="space-y-4">
                        {loading ? (
                            <p className="text-muted-foreground">Loading inventory...</p>
                        ) : inventory.length > 0 ? (
                            inventory.map((lead) => (
                                <InventoryCard key={lead.id} lead={lead} />
                            ))
                        ) : (
                            <p className="text-muted-foreground">No inventory available.</p>
                        )}
                    </div>
                </div>

                {/* Right Column: Buyer Matches */}
                <div className="space-y-6">
                    <h2 className="text-xl font-semibold">Top Buyer Matches</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {MOCK_BUYERS.map((buyer) => (
                            <BuyerCard
                                key={buyer.name}
                                name={buyer.name}
                                score={buyer.score}
                                criteria={buyer.criteria}
                            />
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}
