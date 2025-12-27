"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Loader2, Map as MapIcon, List as ListIcon, Search } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"

import dynamic from "next/dynamic"
import { columns } from "./columns"
import { DataTable } from "./data-table"
const LeadMap = dynamic(() => import("./LeadMap").then(mod => mod.LeadMap), { ssr: false })
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

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
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

            {view === "list" ? (
                <DataTable columns={columns} data={filteredData} />
            ) : (
                <LeadMap leads={filteredData} />
            )}
        </div>
    )
}
