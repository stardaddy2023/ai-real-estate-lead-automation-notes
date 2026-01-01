"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Loader2, Map as MapIcon, List as ListIcon, Search } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"

import dynamic from "next/dynamic"
import { columns } from "./columns"
import { DataTable } from "./data-table"
import { GoogleScoutMap } from "@/components/scout/GoogleScoutMap"
// const LeadMap = dynamic(() => import("./LeadMap").then(mod => mod.LeadMap), { ssr: false })
import { Lead } from "@/types"

async function getLeads(): Promise<Lead[]> {
    // In a real app, this would be an environment variable
    const res = await fetch("http://127.0.0.1:8000/api/v1/leads")
    if (!res.ok) {
        throw new Error("Failed to fetch leads")
    }
    return res.json()
}

export function LeadInbox() {
    const [view, setView] = useState<"list" | "map">("list")
    const [searchQuery, setSearchQuery] = useState("")

    const { data, isLoading, error } = useQuery({
        queryKey: ["leads"],
        queryFn: getLeads,
    })

    if (isLoading) {
        return (
            <div className="flex h-[400px] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        )
    }

    if (error) {
        return (
            <div className="flex h-[400px] items-center justify-center text-red-500">
                Error loading leads: {error.message}
            </div>
        )
    }

    const filteredData = data?.filter(lead =>
        lead.address_street.toLowerCase().includes(searchQuery.toLowerCase()) ||
        lead.owner_name?.toLowerCase().includes(searchQuery.toLowerCase())
    ) || []

    // Map Lead to ScoutResult for GoogleScoutMap
    const mapLeads: any[] = filteredData.map(lead => ({
        id: lead.id,
        address: lead.address_street,
        owner_name: lead.owner_name || "Unknown",
        mailing_address: "N/A", // Not in Lead type
        property_type: "Unknown",
        distress_signals: [],
        distress_score: lead.distress_score,
        // Mock coordinates if missing (same logic as old LeadMap)
        latitude: 32.2226 + (Math.random() - 0.5) * 0.1,
        longitude: -110.9747 + (Math.random() - 0.5) * 0.1,
    }))

    return (
        <div className="space-y-4 h-full flex flex-col">
            <div className="flex items-center justify-between shrink-0">
                <h2 className="text-2xl font-bold tracking-tight">Lead Inbox</h2>
                <div className="flex items-center gap-4">
                    <div className="relative w-64">
                        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search address or owner..."
                            className="pl-8"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                    <Tabs value={view} onValueChange={(v) => setView(v as "list" | "map")}>
                        <TabsList>
                            <TabsTrigger value="list"><ListIcon className="mr-2 h-4 w-4" />List</TabsTrigger>
                            <TabsTrigger value="map"><MapIcon className="mr-2 h-4 w-4" />Map</TabsTrigger>
                        </TabsList>
                    </Tabs>
                </div>
            </div>

            <div className="flex-1 min-h-0 relative rounded-lg border overflow-hidden">
                {view === "list" ? (
                    <div className="h-full overflow-auto p-1">
                        <DataTable columns={columns} data={filteredData} />
                    </div>
                ) : (
                    <div className="h-full w-full absolute inset-0">
                        <GoogleScoutMap
                            leads={mapLeads}
                            onMarkerClick={(lead: any) => console.log("Clicked lead:", lead)}
                        />
                    </div>
                )}
            </div>
        </div>
    )
}
