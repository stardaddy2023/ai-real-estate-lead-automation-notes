"use client"

import { useState, useRef } from 'react'
import dynamic from 'next/dynamic'
import AutocompleteInput from '@/components/ui/AutocompleteInput'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2, Map as MapIcon, List as ListIcon, Download, Search, X } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
import { LeadDetailDialog } from './LeadDetailDialog'
import { LeadFilters, PROPERTY_TYPES, DISTRESS_TYPES, DISABLED_DISTRESS_TYPES } from './LeadFilters'

// Dynamic import for Map to avoid SSR issues
const GoogleScoutMap = dynamic(() => import('./GoogleScoutMap').then(mod => mod.GoogleScoutMap), {
    ssr: false,
    loading: () => <div className="w-full h-full bg-gray-900 animate-pulse flex items-center justify-center text-gray-500">Loading Map...</div>
})

export interface ScoutResult {
    id: string
    address: string
    owner_name: string
    mailing_address: string
    property_type: string
    last_sale_date?: string
    last_sale_price?: number
    assessed_value?: number
    year_built?: number
    sqft?: number
    lot_size?: number
    distress_signals: string[]
    distress_score: number
    latitude: number
    longitude: number
    // Enhanced fields
    beds?: number
    baths?: number
    pool?: boolean
    garage?: boolean
    arv?: number
    phone?: string
    email?: string
    parcel_id?: string
    // Violation consolidation fields
    violation_count?: number
    violations?: Array<{ description: string; activity_num: string }>
}



export default function LeadScout() {
    // State
    const [query, setQuery] = useState("")
    const [results, setResults] = useState<ScoutResult[]>([])
    const [loading, setLoading] = useState(false)
    const [hoveredLeadId, setHoveredLeadId] = useState<string | null>(null)
    const [highlightedLeadId, setHighlightedLeadId] = useState<string | null>(null)
    const [panToLeadId, setPanToLeadId] = useState<string | null>(null)

    // Filters
    const [selectedPropertyTypes, setSelectedPropertyTypes] = useState<string[]>([])
    const [selectedDistressTypes, setSelectedDistressTypes] = useState<string[]>([])
    const [minBeds, setMinBeds] = useState<string>("")
    const [minBaths, setMinBaths] = useState<string>("")
    const [minSqft, setMinSqft] = useState<string>("")
    const [maxPrice, setMaxPrice] = useState<string>("")
    const [limit, setLimit] = useState<number>(100)

    const [viewMode, setViewMode] = useState<'list' | 'map'>('map') // Default to Map
    const { toast } = useToast()

    // Detail Dialog State
    const [selectedLead, setSelectedLead] = useState<ScoutResult | null>(null)
    const [isDetailOpen, setIsDetailOpen] = useState(false)

    // Refs for scrolling
    const listRef = useRef<HTMLDivElement>(null)

    // Search Handler
    const handleSearch = async () => {
        setLoading(true)
        setResults([]) // Clear previous results
        setPanToLeadId(null) // Reset pan state

        try {
            const term = query.trim()
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const payload: any = {
                property_types: selectedPropertyTypes.length > 0 ? selectedPropertyTypes : ["Single Family"],
                distress_type: selectedDistressTypes, // Allow empty list for generic search
                limit: limit
            }

            // Smart Classification
            if (/^\d{5}(-\d{4})?$/.test(term)) {
                payload.zip_code = term
            } else if (/county$/i.test(term)) {
                payload.county = term.replace(/ county$/i, "").trim()
            } else if (/^\d/.test(term)) {
                payload.address = term
            } else {
                // Assume City if not starting with number
                payload.city = term
            }

            console.log("Sending Search Payload:", payload)

            const res = await fetch('http://localhost:8000/scout/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })

            if (!res.ok) {
                const errorText = await res.text()
                console.error("Search API Error:", res.status, errorText)
                throw new Error(`Search failed: ${res.status}`)
            }

            const data = await res.json()
            console.log("Search Results:", data) // Debug log
            setResults(data)

            if (data.length === 0) {
                toast({ title: "No leads found", description: "Try adjusting your filters." })
            } else {
                toast({ title: `Found ${data.length} leads`, description: "Map updated." })
            }

        } catch (error) {
            console.error("Handle Search Error:", error)
            toast({ title: "Error", description: "Failed to fetch leads.", variant: "destructive" })
        } finally {
            setLoading(false)
        }
    }

    const handleImport = async (lead: ScoutResult) => {
        try {
            const res = await fetch('http://localhost:8000/leads/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    address: lead.address,
                    owner_name: lead.owner_name,
                    mailing_address: lead.mailing_address,
                    property_type: lead.property_type,
                    equity_value: lead.assessed_value, // Proxy
                    status: "New",
                    notes: `Scouted via LeadScout. Distress: ${lead.distress_signals.join(', ')}`
                })
            })

            if (res.ok) {
                toast({ title: "Lead Imported", description: `${lead.address} added to Inbox.` })
            }
        } catch (error) {
            toast({ title: "Import failed", variant: "destructive" })
        }
    }

    // Bulk Selection State
    const [selectedLeadIds, setSelectedLeadIds] = useState<Set<string>>(new Set())

    const toggleSelectLead = (id: string) => {
        const newSelected = new Set(selectedLeadIds)
        if (newSelected.has(id)) {
            newSelected.delete(id)
        } else {
            newSelected.add(id)
        }
        setSelectedLeadIds(newSelected)
    }

    const toggleSelectAll = () => {
        if (selectedLeadIds.size === results.length) {
            setSelectedLeadIds(new Set())
        } else {
            setSelectedLeadIds(new Set(results.map(r => r.id)))
        }
    }

    const handleBulkImport = async () => {
        if (selectedLeadIds.size === 0) return

        let successCount = 0
        setLoading(true)

        for (const id of Array.from(selectedLeadIds)) {
            const lead = results.find(r => r.id === id)
            if (lead) {
                await handleImport(lead)
                successCount++
            }
        }

        setLoading(false)
        toast({ title: "Bulk Import Complete", description: `Imported ${successCount} leads.` })
        setSelectedLeadIds(new Set())
    }

    // Toggle Filters
    const togglePropertyType = (type: string) => {
        setSelectedPropertyTypes(prev =>
            prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]
        )
    }

    const toggleDistressType = (type: string) => {
        setSelectedDistressTypes(prev =>
            prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]
        )
    }

    // Sync Map Click to List Scroll
    const handleMarkerClick = (lead: ScoutResult) => {
        setHighlightedLeadId(lead.id)
        setPanToLeadId(lead.id) // Pan on marker click too
        setViewMode('list')

        // Scroll to item in list
        setTimeout(() => {
            const element = document.getElementById(`lead-card-${lead.id}`)
            if (element) {
                element.scrollIntoView({ behavior: 'smooth', block: 'center' })
            }
        }, 100)
    }

    const handleMapClick = () => {
        setViewMode('map')
        setHighlightedLeadId(null)
        setPanToLeadId(null)
    }

    return (
        <div className="flex h-screen w-full bg-black text-white overflow-hidden relative">

            {/* SEARCH BAR (Floating & Dynamic Position) */}
            <div className={`absolute top-4 z-50 w-full max-w-2xl px-4 transition-all duration-300 ease-in-out ${viewMode === 'list' ? 'left-[calc(50%-12rem)]' : 'left-1/2'} -translate-x-1/2 transform pointer-events-none`}>
                <div className="pointer-events-auto flex flex-col items-center w-full">
                    <div className="bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-md shadow-lg flex items-center px-3 h-10 gap-2 w-full">

                        {/* Search Icon (Left) */}
                        <Search className="text-gray-400 w-4 h-4 shrink-0" />

                        {/* Location Input */}
                        <div className="flex-1 min-w-[200px] h-full">
                            <AutocompleteInput
                                value={query}
                                onChange={setQuery}
                                onSearch={handleSearch}
                                placeholder="Search Zip Code, City, or Neighborhood..."
                                className="h-full w-full"
                                inputClassName="bg-transparent border-none focus:ring-0 text-gray-900 dark:text-white placeholder:text-gray-400 h-full w-full focus:outline-none text-sm px-0"
                                showIcon={false}
                            />
                        </div>

                        <div className="h-4 w-px bg-gray-200 dark:bg-gray-800 mx-1 hidden md:block" />

                        {/* Limit Selector */}
                        <select
                            className="bg-transparent border-none text-gray-700 dark:text-gray-300 text-sm focus:outline-none cursor-pointer hover:text-gray-900 dark:hover:text-white transition-colors font-medium"
                            value={limit}
                            onChange={(e) => setLimit(Number(e.target.value))}
                        >
                            <option value={10} className="bg-white dark:bg-gray-900">10 Leads</option>
                            <option value={25} className="bg-white dark:bg-gray-900">25 Leads</option>
                            <option value={50} className="bg-white dark:bg-gray-900">50 Leads</option>
                            <option value={100} className="bg-white dark:bg-gray-900">100 Leads</option>
                            <option value={500} className="bg-white dark:bg-gray-900">500 Leads</option>
                        </select>

                        {/* Bulk Import Button */}
                        {selectedLeadIds.size > 0 && (
                            <Button
                                variant="default"
                                size="sm"
                                onClick={handleBulkImport}
                                className="bg-green-600 hover:bg-green-700 text-white rounded-md h-7 text-xs px-2 ml-2"
                            >
                                Import ({selectedLeadIds.size})
                            </Button>
                        )}
                    </div>

                    {/* ACTIVE FILTERS (TAGS) */}
                    {(selectedPropertyTypes.length > 0 || selectedDistressTypes.length > 0) && (
                        <div className="flex flex-wrap gap-2 mt-2 justify-center w-full pointer-events-auto">
                            {selectedPropertyTypes.map(type => (
                                <Badge key={type} variant="secondary" className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm text-gray-800 dark:text-gray-200 border border-gray-200 dark:border-gray-700 shadow-sm hover:bg-white dark:hover:bg-gray-800 pl-2 pr-1 py-0.5 gap-1 cursor-pointer" onClick={() => togglePropertyType(type)}>
                                    {type}
                                    <X className="w-3 h-3 text-gray-400 hover:text-red-500" />
                                </Badge>
                            ))}
                            {selectedDistressTypes.map(type => (
                                <Badge key={type} variant="secondary" className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm text-red-600 dark:text-red-400 border border-red-200 dark:border-red-900/50 shadow-sm hover:bg-white dark:hover:bg-gray-800 pl-2 pr-1 py-0.5 gap-1 cursor-pointer" onClick={() => toggleDistressType(type)}>
                                    {type}
                                    <X className="w-3 h-3 text-red-400 hover:text-red-600" />
                                </Badge>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* RIGHT SIDE CONTROLS (Filters) */}
            <div className="absolute top-4 right-4 z-50 pointer-events-auto flex items-center gap-2">
                <LeadFilters
                    selectedPropertyTypes={selectedPropertyTypes}
                    setSelectedPropertyTypes={setSelectedPropertyTypes}
                    selectedDistressTypes={selectedDistressTypes}
                    setSelectedDistressTypes={setSelectedDistressTypes}
                    minBeds={minBeds}
                    setMinBeds={setMinBeds}
                    minBaths={minBaths}
                    setMinBaths={setMinBaths}
                    minSqft={minSqft}
                    setMinSqft={setMinSqft}
                    onSearch={handleSearch}
                />
            </div>

            {/* MAIN CONTENT AREA */}
            <div className="flex-1 relative h-full">

                {/* LIST VIEW OVERLAY (Visible when viewMode is 'list') */}
                <div className={`absolute top-0 right-0 bottom-0 w-96 bg-gray-950/90 backdrop-blur-md border-l border-gray-800 z-10 transition-transform duration-300 ease-in-out ${viewMode === 'list' ? 'translate-x-0' : 'translate-x-full'} pt-0`}>
                    <div className="p-4 border-b border-gray-800 flex justify-between items-center bg-gray-900/50 backdrop-blur-sm">
                        <div className="flex items-center gap-3">
                            <h2 className="font-semibold text-gray-200">RESULTS ({results.length})</h2>
                            {results.length > 0 && (
                                <div className="flex items-center gap-2 ml-4">
                                    <input
                                        type="checkbox"
                                        id="select-all"
                                        className="w-4 h-4 rounded border-gray-600 text-green-600 focus:ring-green-500 bg-gray-700"
                                        checked={results.length > 0 && selectedLeadIds.size === results.length}
                                        onChange={toggleSelectAll}
                                    />
                                    <label htmlFor="select-all" className="text-xs text-gray-400 cursor-pointer select-none">
                                        Select All
                                    </label>
                                </div>
                            )}
                        </div>
                        <div className="flex items-center gap-2">
                            <Button variant="ghost" size="sm" onClick={() => setViewMode('map')}>
                                <MapIcon className="h-4 w-4 mr-2" /> Map
                            </Button>
                        </div>
                    </div>
                    <ScrollArea className="h-[calc(100vh-160px)]" ref={listRef}>
                        <div className="p-4 space-y-3">
                            {results.map(lead => (
                                <Card
                                    key={lead.id}
                                    id={`lead-card-${lead.id}`}
                                    className={`p-4 bg-gray-800/50 border border-gray-700/50 rounded-lg hover:border-green-500/50 transition-all cursor-pointer group relative ${highlightedLeadId === lead.id ? 'ring-2 ring-green-500 bg-gray-800' : ''}`}
                                    onMouseEnter={() => {
                                        setHoveredLeadId(lead.id)
                                        setHighlightedLeadId(lead.id)
                                    }}
                                    onMouseLeave={() => {
                                        setHoveredLeadId(null)
                                        setHighlightedLeadId(null)
                                    }}
                                    onClick={() => {
                                        setSelectedLead(lead)
                                        setPanToLeadId(lead.id) // Pan on card click
                                        setIsDetailOpen(true)
                                    }}
                                >
                                    {/* Bulk Select Checkbox */}
                                    <div className="absolute top-4 left-4 z-10" onClick={(e) => e.stopPropagation()}>
                                        <input
                                            type="checkbox"
                                            className="w-4 h-4 rounded border-gray-600 text-green-600 focus:ring-green-500 bg-gray-700"
                                            checked={selectedLeadIds.has(lead.id)}
                                            onChange={() => toggleSelectLead(lead.id)}
                                        />
                                    </div>

                                    <div className="flex justify-between items-start pl-8">
                                        <div>
                                            <h3 className="font-bold text-white group-hover:text-green-400 transition-colors text-sm">{lead.address}</h3>
                                            <p className="text-xs text-gray-400">APN: {lead.parcel_id || "Unknown"}</p>
                                        </div>
                                        <Button size="icon" variant="ghost" className="h-6 w-6 text-gray-400 hover:text-green-400" onClick={(e) => {
                                            e.stopPropagation()
                                            handleImport(lead)
                                        }}>
                                            <Download className="w-3 h-3" />
                                        </Button>
                                    </div>

                                    <div className="grid grid-cols-2 gap-x-4 gap-y-1 mt-3 text-xs text-gray-500 pl-8">
                                        <div className="flex justify-between">
                                            <span>Est. Value</span>
                                            <span className="text-white font-mono">{lead.arv ? `$${lead.arv.toLocaleString()}` : "N/A"}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>SqFt</span>
                                            <span className="text-white">{lead.sqft ? lead.sqft.toLocaleString() : "-"}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>Beds/Baths</span>
                                            <span className="text-white">{lead.beds || "-"}/{lead.baths || "-"}</span>
                                        </div>
                                    </div>

                                    <div className="flex flex-wrap gap-1 mt-2 pl-8">
                                        {lead.property_type && lead.property_type !== "Unknown" && (
                                            <Badge variant="outline" className="text-[10px] border-gray-700 text-gray-400">
                                                {lead.property_type}
                                            </Badge>
                                        )}
                                        {lead.distress_signals?.map((s, i) => (
                                            <Badge key={i} variant="outline" className="text-[10px] border-red-900 text-red-400 bg-red-950/30">
                                                {s === "Code Violation" && (lead.violation_count ?? 0) > 1
                                                    ? `Code Violations (${lead.violation_count})`
                                                    : s}
                                            </Badge>
                                        ))}
                                    </div>
                                </Card>
                            ))}
                        </div>
                    </ScrollArea>
                </div>

                {/* MAP BACKGROUND */}
                <div className="absolute inset-0 z-0">
                    <GoogleScoutMap
                        leads={results}
                        highlightedLeadId={highlightedLeadId}
                        panToLeadId={panToLeadId}
                        onMarkerClick={handleMarkerClick}
                        onMapClick={handleMapClick}
                    />
                </div>

                {/* LOADING OVERLAY */}
                {loading && (
                    <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm pointer-events-none">
                        <div className="bg-white dark:bg-gray-900 p-4 rounded-full shadow-2xl flex items-center gap-3 border border-gray-200 dark:border-gray-800">
                            <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
                            <span className="font-medium text-gray-900 dark:text-gray-100">Scouting Area...</span>
                        </div>
                    </div>
                )}

                {/* "Show List" Toggle Button (Bottom Center) */}
                {viewMode === 'map' && results.length > 0 && (
                    <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-50">
                        <Button
                            onClick={() => setViewMode('list')}
                            className="rounded-full shadow-2xl bg-blue-600 hover:bg-blue-700 text-white border-none px-8 py-6 text-lg font-semibold transition-all transform hover:scale-105"
                        >
                            <ListIcon className="w-5 h-5 mr-2" />
                            Show {results.length} Results
                        </Button>
                    </div>
                )}
            </div>

            {/* Detail Dialog */}
            <LeadDetailDialog
                lead={selectedLead}
                open={isDetailOpen}
                onOpenChange={setIsDetailOpen}
            />
        </div>
    )
}
