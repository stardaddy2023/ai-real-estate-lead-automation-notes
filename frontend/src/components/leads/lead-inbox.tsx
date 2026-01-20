"use client"

import { useState, useMemo } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Loader2, Map as MapIcon, List as ListIcon, Search, Zap, RefreshCw } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useToast } from "@/components/ui/use-toast"

import dynamic from "next/dynamic"
import { createInboxColumns } from "./columns"
import { DataTable } from "./data-table"
import { GoogleScoutMap } from "@/components/scout/GoogleScoutMap"
import { Lead } from "@/types"

// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

async function getLeads(): Promise<Lead[]> {
    const res = await fetch(`${API_BASE}/api/v1/leads`)
    if (!res.ok) {
        throw new Error("Failed to fetch leads")
    }
    return res.json()
}

export function LeadInbox() {
    const [view, setView] = useState<"list" | "map">("list")
    const [searchQuery, setSearchQuery] = useState("")
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
    const [enrichingIds, setEnrichingIds] = useState<Set<string>>(new Set())

    const { toast } = useToast()
    const queryClient = useQueryClient()

    const { data, isLoading, error, refetch, isFetching } = useQuery({
        queryKey: ["leads"],
        queryFn: getLeads,
    })

    // Filter data by search query
    const filteredData = useMemo(() => {
        if (!data) return []
        if (!searchQuery) return data

        const search = searchQuery.toLowerCase()
        return data.filter(lead =>
            lead.address_street?.toLowerCase().includes(search) ||
            lead.owner_name?.toLowerCase().includes(search) ||
            lead.phone?.includes(search) ||
            lead.email?.toLowerCase().includes(search)
        )
    }, [data, searchQuery])

    // Toggle selection for a single lead
    const toggleSelect = (id: string) => {
        setSelectedIds(prev => {
            const newSet = new Set(prev)
            if (newSet.has(id)) {
                newSet.delete(id)
            } else {
                newSet.add(id)
            }
            return newSet
        })
    }

    // Toggle all leads
    const toggleAll = () => {
        if (selectedIds.size === filteredData.length) {
            setSelectedIds(new Set())
        } else {
            setSelectedIds(new Set(filteredData.map(l => l.id)))
        }
    }

    // Skip trace a single lead
    const handleEnrich = async (lead: Lead) => {
        setEnrichingIds(prev => new Set(prev).add(lead.id))

        try {
            const res = await fetch(`${API_BASE}/leads/${lead.id}/skiptrace`, {
                method: 'POST'
            })

            if (res.ok) {
                const result = await res.json()
                if (result.skip_trace_status === "found") {
                    toast({
                        title: "Skip Trace Complete",
                        description: `Found contact info for ${lead.address_street}`
                    })
                } else {
                    toast({
                        title: "No Contact Info Found",
                        description: result.skip_trace_message || "No phone or email found",
                        variant: "default"
                    })
                }
                // Refresh leads list
                queryClient.invalidateQueries({ queryKey: ["leads"] })
            } else {
                throw new Error("Skip trace failed")
            }
        } catch (error) {
            toast({ title: "Skip Trace Failed", variant: "destructive" })
        } finally {
            setEnrichingIds(prev => {
                const newSet = new Set(prev)
                newSet.delete(lead.id)
                return newSet
            })
        }
    }

    // Bulk skip trace selected leads
    const handleBulkEnrich = async () => {
        if (selectedIds.size === 0) return

        const leadsToEnrich = filteredData.filter(l => selectedIds.has(l.id))
        let successCount = 0

        for (const lead of leadsToEnrich) {
            setEnrichingIds(prev => new Set(prev).add(lead.id))

            try {
                const res = await fetch(`${API_BASE}/leads/${lead.id}/skiptrace`, {
                    method: 'POST'
                })
                if (res.ok) successCount++
            } catch (error) {
                // Continue with next lead
            } finally {
                setEnrichingIds(prev => {
                    const newSet = new Set(prev)
                    newSet.delete(lead.id)
                    return newSet
                })
            }
        }

        toast({
            title: "Bulk Skip Trace Complete",
            description: `Enriched ${successCount} of ${selectedIds.size} leads`
        })

        setSelectedIds(new Set())
        queryClient.invalidateQueries({ queryKey: ["leads"] })
    }

    // Create columns with callbacks
    const inboxColumns = useMemo(() => createInboxColumns({
        onEnrich: handleEnrich,
        enrichingIds,
        selectedIds,
        onToggleSelect: toggleSelect,
        onToggleAll: toggleAll,
        allSelected: filteredData.length > 0 && selectedIds.size === filteredData.length
    }), [enrichingIds, selectedIds, filteredData])

    // Map leads to format expected by GoogleScoutMap
    const mapLeads = useMemo(() => filteredData.map(lead => ({
        id: lead.id,
        address: lead.address_street,
        owner_name: lead.owner_name || "Unknown",
        mailing_address: lead.mailing_address || "N/A",
        property_type: lead.property_type || "Unknown",
        distress_signals: [],
        distress_score: lead.distress_score || 0,
        latitude: lead.latitude || 32.2226 + (Math.random() - 0.5) * 0.1,
        longitude: lead.longitude || -110.9747 + (Math.random() - 0.5) * 0.1,
    })), [filteredData])

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

    return (
        <div className="space-y-4 h-full flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between shrink-0 flex-wrap gap-4">
                <div className="flex items-center gap-4">
                    <h2 className="text-2xl font-bold tracking-tight">Lead Inbox</h2>
                    <span className="text-sm text-gray-500">
                        {filteredData.length} leads {selectedIds.size > 0 && `(${selectedIds.size} selected)`}
                    </span>
                </div>

                <div className="flex items-center gap-4 flex-wrap">
                    {/* Bulk Actions */}
                    {selectedIds.size > 0 && (
                        <Button
                            onClick={handleBulkEnrich}
                            disabled={enrichingIds.size > 0}
                            className="bg-yellow-600 hover:bg-yellow-700"
                        >
                            <Zap className="mr-2 h-4 w-4" />
                            Skip Trace ({selectedIds.size})
                        </Button>
                    )}

                    {/* Refresh Button */}
                    <Button variant="outline" size="icon" onClick={() => refetch()} disabled={isFetching}>
                        <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
                    </Button>

                    {/* Search */}
                    <div className="relative w-64">
                        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search address, owner, phone..."
                            className="pl-8"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>

                    {/* View Toggle */}
                    <Tabs value={view} onValueChange={(v) => setView(v as "list" | "map")}>
                        <TabsList>
                            <TabsTrigger value="list"><ListIcon className="mr-2 h-4 w-4" />List</TabsTrigger>
                            <TabsTrigger value="map"><MapIcon className="mr-2 h-4 w-4" />Map</TabsTrigger>
                        </TabsList>
                    </Tabs>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 min-h-0 relative rounded-lg border overflow-hidden">
                {view === "list" ? (
                    <div className="h-full overflow-auto p-1">
                        <DataTable columns={inboxColumns} data={filteredData} />
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
