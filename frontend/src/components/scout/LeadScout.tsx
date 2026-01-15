"use client"

import { useState, useRef, useMemo } from 'react'
import dynamic from 'next/dynamic'
import AutocompleteInput from '@/components/ui/AutocompleteInput'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Loader2, Map as MapIcon, List as ListIcon, Download, Search, X, SlidersHorizontal, LayoutGrid } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger, SheetClose } from '@/components/ui/sheet'
import { LeadDetailDialog } from './LeadDetailDialog'
import { LeadFilters, PROPERTY_TYPES, DISTRESS_TYPES, DISABLED_DISTRESS_TYPES, HOT_LIST_TYPES } from './LeadFilters'
import { useAppStore, ScoutResult } from '@/lib/store'
import { DataTable } from '@/components/leads/data-table'
import { createScoutColumns } from './scout-columns'


// Helper to get human-readable flood zone description
const getFloodZoneDescription = (zone: string | undefined) => {
    if (!zone) return "Unknown"
    const z = zone.toUpperCase()
    if (z.includes("X")) return "Minimal Risk (Zone X)"
    if (z.includes("AE")) return "High Risk (1% Annual Chance)"
    if (z.includes("A")) return "High Risk (No BFE)"
    if (z.includes("AH")) return "High Risk (Shallow Flooding)"
    if (z.includes("AO")) return "High Risk (Sheet Flow)"
    if (z.includes("D")) return "Undetermined Risk"
    return `Zone ${zone}`
}

// Dynamic import for Map to avoid SSR issues
const GoogleScoutMap = dynamic(() => import('./GoogleScoutMap').then(mod => mod.GoogleScoutMap), {
    ssr: false,
    loading: () => <div className="w-full h-full bg-gray-900 animate-pulse flex items-center justify-center text-gray-500">Loading Map...</div>
})

export default function LeadScout() {
    // Global State
    const { leadScout, setLeadScoutState } = useAppStore()
    const {
        query, results, loading,
        selectedPropertyTypes, selectedDistressTypes,
        limit, minBeds, minBaths, minSqft,
        viewMode, highlightedLeadId, panToLeadId, selectedLeadIds,
        bounds
    } = leadScout

    const { toast } = useToast()

    // Local State (UI only)
    const [selectedLead, setSelectedLead] = useState<ScoutResult | null>(null)
    const [isDetailOpen, setIsDetailOpen] = useState(false)
    const [hoveredLeadId, setHoveredLeadId] = useState<string | null>(null)
    const [includePropertyDetails, setIncludePropertyDetails] = useState(false) // Default OFF for fast mode
    const [selectedHotList, setSelectedHotList] = useState<string[]>([]) // Hot List filters

    // Create scout columns with callbacks
    const scoutColumns = useMemo(() => createScoutColumns({
        onViewDetails: (lead) => {
            setSelectedLead(lead)
            setIsDetailOpen(true)
        },
        onImport: (lead) => handleImport(lead)
    }), [])

    // Compute selected lead index for navigation
    const selectedLeadIndex = selectedLead ? results.findIndex(r => r.id === selectedLead.id) : -1


    // Lead navigation handlers
    const handleNextLead = () => {
        if (selectedLeadIndex >= 0 && selectedLeadIndex < results.length - 1) {
            setSelectedLead(results[selectedLeadIndex + 1])
        }
    }
    const handlePrevLead = () => {
        if (selectedLeadIndex > 0) {
            setSelectedLead(results[selectedLeadIndex - 1])
        }
    }

    // Refs
    const listRef = useRef<HTMLDivElement>(null)
    const abortControllerRef = useRef<AbortController | null>(null)

    // Search Handler
    const handleSearch = async (clearBounds = true, explicitBounds: any = null, ignoreQuery = false) => {
        // Cancel previous search if running
        if (abortControllerRef.current) {
            abortControllerRef.current.abort()
        }

        // Create new controller
        const controller = new AbortController()
        abortControllerRef.current = controller

        // If clearBounds is true (text search), reset bounds to null
        // If explicitBounds is provided, use it (Search Area button)
        // Otherwise use current state bounds (Filter update)
        const newBounds = explicitBounds || (clearBounds ? null : bounds)

        // If ignoring query (e.g. Map Search), clear it from state too
        if (ignoreQuery) {
            setLeadScoutState({ query: "" })
        }

        setLeadScoutState({ loading: true, results: [], panToLeadId: null, bounds: newBounds })

        try {
            const term = ignoreQuery ? "" : query.trim()
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const payload: any = {
                property_types: selectedPropertyTypes,
                distress_type: selectedDistressTypes, // Allow empty list for generic search
                hot_list: selectedHotList, // FSBO, Price Reduced, High DOM, New Listing
                limit: limit,
                bounds: newBounds, // Include bounds in payload
                skip_homeharvest: !includePropertyDetails // Fast mode when toggle is OFF
            }

            // Smart Classification
            if (term) {
                if (/^\d{5}(-\d{4})?$/.test(term)) {
                    payload.zip_code = term
                } else if (/county$/i.test(term)) {
                    payload.county = term.replace(/ county$/i, "").trim()
                } else if (/^\d/.test(term)) {
                    payload.address = term
                } else {
                    // Check if it's a known city, otherwise treat as Neighborhood
                    const KNOWN_CITIES = ["TUCSON", "MARANA", "ORO VALLEY", "VAIL", "SAHUARITA", "SOUTH TUCSON", "CATALINA FOOTHILLS", "CASAS ADOBES", "DREXEL HEIGHTS", "FLOWING WELLS", "TANQUE VERDE", "TUCSON ESTATES", "GREEN VALLEY"]
                    if (KNOWN_CITIES.some(city => term.toUpperCase() === city)) {
                        payload.city = term
                    } else {
                        // Assume Neighborhood/Subdivision
                        payload.neighborhood = term
                    }
                }
            }

            console.log("DEBUG: handleSearch called. Query:", term)
            console.log("DEBUG: Payload prepared:", payload)

            const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'
            console.log(`DEBUG: Initiating fetch to ${API_BASE_URL}/scout/search...`)
            const res = await fetch(`${API_BASE_URL}/scout/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                signal: controller.signal
            })

            if (!res.ok) {
                const errorText = await res.text()
                console.error("Search API Error:", res.status, errorText)
                throw new Error(`Search failed: ${res.status}`)
            }

            const data = await res.json()
            console.log("Search Results:", data) // Debug log

            let leads = []
            let warning = null

            if (Array.isArray(data)) {
                leads = data
            } else if (data.leads) {
                leads = data.leads
                warning = data.warning
            }

            setLeadScoutState({ results: leads, loading: false })

            if (warning) {
                toast({
                    title: "Notice",
                    description: warning,
                    variant: "destructive", // Use destructive to grab attention
                    duration: 5000
                })
            } else if (leads.length === 0) {
                toast({ title: "No leads found", description: "Try adjusting your filters." })
            } else {
                toast({ title: `Found ${leads.length} leads`, description: "Map updated." })
            }

        } catch (error: any) {
            if (error.name === 'AbortError') {
                console.log("Search cancelled")
                setLeadScoutState({ loading: false })
                return
            }
            console.error("Handle Search Error:", error)
            toast({ title: "Error", description: "Failed to fetch leads.", variant: "destructive" })
            setLeadScoutState({ loading: false })
        } finally {
            if (abortControllerRef.current === controller) {
                abortControllerRef.current = null
            }
        }
    }

    const handleCancelSearch = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort()
            setLeadScoutState({ loading: false })
            toast({ title: "Search Cancelled", description: "Operation stopped by user." })
        }
    }

    const handleImport = async (lead: ScoutResult) => {
        try {
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
            const res = await fetch(`${baseUrl}/api/v1/leads`, {
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

    // Bulk Selection
    const toggleSelectLead = (id: string) => {
        const newSelected = new Set(selectedLeadIds)
        if (newSelected.has(id)) {
            newSelected.delete(id)
        } else {
            newSelected.add(id)
        }
        setLeadScoutState({ selectedLeadIds: newSelected })
    }

    const toggleSelectAll = () => {
        if (selectedLeadIds.size === results.length) {
            setLeadScoutState({ selectedLeadIds: new Set() })
        } else {
            setLeadScoutState({ selectedLeadIds: new Set(results.map(r => r.id)) })
        }
    }

    const handleBulkImport = async () => {
        if (selectedLeadIds.size === 0) return

        let successCount = 0
        setLeadScoutState({ loading: true })

        for (const id of Array.from(selectedLeadIds)) {
            const lead = results.find(r => r.id === id)
            if (lead) {
                await handleImport(lead)
                successCount++
            }
        }

        setLeadScoutState({ loading: false, selectedLeadIds: new Set() })
        toast({ title: "Bulk Import Complete", description: `Imported ${successCount} leads.` })
    }

    // Toggle Filters
    const togglePropertyType = (type: string) => {
        setLeadScoutState({
            selectedPropertyTypes: selectedPropertyTypes.includes(type)
                ? selectedPropertyTypes.filter(t => t !== type)
                : [...selectedPropertyTypes, type]
        })
    }

    const toggleDistressType = (type: string) => {
        setLeadScoutState({
            selectedDistressTypes: selectedDistressTypes.includes(type)
                ? selectedDistressTypes.filter(t => t !== type)
                : [...selectedDistressTypes, type]
        })
    }

    // Map Interactions
    const handleMarkerClick = (lead: ScoutResult) => {
        setLeadScoutState({ highlightedLeadId: lead.id, panToLeadId: lead.id, viewMode: 'list' })

        // Scroll to item in list
        setTimeout(() => {
            const element = document.getElementById(`lead-card-${lead.id}`)
            if (element) {
                element.scrollIntoView({ behavior: 'smooth', block: 'center' })
            }
        }, 100)
    }

    const handleMapClick = () => {
        setLeadScoutState({ viewMode: 'map', highlightedLeadId: null, panToLeadId: null })
    }

    const handleMapSelection = (newBounds: { north: number, south: number, east: number, west: number } | null) => {
        setLeadScoutState({ bounds: newBounds })

        // If drawing a box, clear the text search query to avoid confusion
        if (newBounds) {
            setLeadScoutState({ query: "" })
        }

        // Do NOT trigger search automatically. 
        // User must click "Search Area" button or hit Enter.
    }

    // Explicit handler for "Search Area" button
    const handleSearchArea = (searchBounds: any) => {
        handleSearch(false, searchBounds, true)
    }

    const handleHotListChange = (newFilters: string[]) => {
        setSelectedHotList(newFilters)

        // Auto-enable Details if MLS filter is selected
        const mlsFilters = ["FSBO", "Price Reduced", "High Days on Market", "New Listing"]
        const hasMlsFilter = newFilters.some(f => mlsFilters.includes(f))

        if (hasMlsFilter && !includePropertyDetails) {
            setIncludePropertyDetails(true)
            toast({
                title: "Details Enabled",
                description: "MLS filters require detailed property data.",
                duration: 3000
            })
        }
    }

    return (
        <div className="flex h-screen w-full bg-black text-white overflow-hidden relative">
            {/* Error Alert */}
            {leadScout.error && (
                <div className="absolute top-0 left-0 right-0 z-[60] bg-red-500 text-white px-4 py-2 text-sm font-medium text-center animate-in slide-in-from-top flex items-center justify-center gap-2">
                    <span>{leadScout.error}</span>
                    <button
                        onClick={() => setLeadScoutState({ error: null })}
                        className="p-1 hover:bg-white/20 rounded"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>
            )}

            {/* SEARCH BAR (Floating & Dynamic Position) */}
            <div className={`absolute top-4 z-50 w-[calc(100%-1rem)] md:w-full max-w-4xl px-0 md:px-4 transition-all duration-300 ease-in-out ${viewMode === 'list' ? 'left-1/2 md:left-[calc(50%-12rem)]' : 'left-1/2'} -translate-x-1/2 transform pointer-events-none`}>
                <div className="pointer-events-auto flex flex-col items-center w-full">

                    {/* DESKTOP LAYOUT (Hidden on Mobile) */}
                    <div className="hidden md:flex bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-md shadow-lg items-center px-3 h-10 gap-2 w-full">
                        <Search className="text-gray-400 w-4 h-4 shrink-0" />
                        <div className="flex-1 min-w-[150px] h-full">
                            <AutocompleteInput
                                value={query}
                                onChange={(val) => {
                                    setLeadScoutState({ query: val })
                                    if (val && bounds) setLeadScoutState({ bounds: null })
                                }}
                                onSearch={() => handleSearch(true)}
                                placeholder="Search Zip Code, City, or Neighborhood..."
                                className="h-full w-full"
                                inputClassName="bg-transparent border-none focus:ring-0 text-gray-900 dark:text-white placeholder:text-gray-400 h-full w-full focus:outline-none text-sm px-0"
                                showIcon={false}
                            />
                        </div>
                        <div className="h-4 w-px bg-gray-200 dark:bg-gray-800 mx-1" />
                        <select
                            className="bg-transparent border-none text-gray-700 dark:text-gray-300 text-sm focus:outline-none cursor-pointer hover:text-gray-900 dark:hover:text-white transition-colors font-medium"
                            value={limit}
                            onChange={(e) => setLeadScoutState({ limit: Number(e.target.value) })}
                        >
                            <option value={10} className="bg-white dark:bg-gray-900">10 Leads</option>
                            <option value={25} className="bg-white dark:bg-gray-900">25 Leads</option>
                            <option value={50} className="bg-white dark:bg-gray-900">50 Leads</option>
                            <option value={100} className="bg-white dark:bg-gray-900">100 Leads</option>
                            <option value={500} className="bg-white dark:bg-gray-900">500 Leads</option>
                        </select>
                        <div className="h-4 w-px bg-gray-200 dark:bg-gray-800 mx-1" />
                        <LeadFilters
                            selectedPropertyTypes={selectedPropertyTypes}
                            setSelectedPropertyTypes={(val) => setLeadScoutState({ selectedPropertyTypes: val })}
                            selectedDistressTypes={selectedDistressTypes}
                            setSelectedDistressTypes={(val) => setLeadScoutState({ selectedDistressTypes: val })}
                            selectedHotList={selectedHotList}
                            setSelectedHotList={handleHotListChange}
                            minBeds={minBeds}
                            setMinBeds={(val) => setLeadScoutState({ minBeds: val })}
                            minBaths={minBaths}
                            setMinBaths={(val) => setLeadScoutState({ minBaths: val })}
                            minSqft={minSqft}
                            setMinSqft={(val) => setLeadScoutState({ minSqft: val })}
                            onSearch={() => handleSearch(false)}
                        />
                        <div className="h-4 w-px bg-gray-200 dark:bg-gray-800 mx-1" />
                        <label className="flex items-center gap-1.5 cursor-pointer shrink-0" title="When enabled, fetches detailed property info (beds, baths, sqft, photos) - adds ~45s to search">
                            <input
                                type="checkbox"
                                checked={includePropertyDetails}
                                onChange={(e) => setIncludePropertyDetails(e.target.checked)}
                                className="w-3.5 h-3.5 rounded border-gray-400 text-green-600 focus:ring-green-500 focus:ring-1"
                            />
                            <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">Details</span>
                        </label>
                        <Button
                            size="sm"
                            className="h-8 bg-green-600 hover:bg-green-700 text-white px-4 shrink-0"
                            onClick={() => query ? handleSearch(true) : handleSearch(false)}
                        >
                            Search
                        </Button>
                        <div className="h-4 w-px bg-gray-200 dark:bg-gray-800 mx-1" />
                        <Tabs value={viewMode} onValueChange={(v) => setLeadScoutState({ viewMode: v as 'map' | 'list' })} className="shrink-0">
                            <TabsList className="h-8 bg-gray-100 dark:bg-gray-800 p-0.5">
                                <TabsTrigger value="list" className="h-7 px-2 text-xs data-[state=active]:bg-white dark:data-[state=active]:bg-gray-700">
                                    <ListIcon className="w-3.5 h-3.5 mr-1" />
                                    List
                                </TabsTrigger>
                                <TabsTrigger value="map" className="h-7 px-2 text-xs data-[state=active]:bg-white dark:data-[state=active]:bg-gray-700">
                                    <MapIcon className="w-3.5 h-3.5 mr-1" />
                                    Map
                                </TabsTrigger>
                            </TabsList>
                        </Tabs>
                    </div>


                    {/* MOBILE LAYOUT (Visible on Mobile) */}
                    <div className="flex md:hidden bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-full shadow-lg items-center px-4 h-12 w-full gap-3">
                        <Search className="text-gray-400 w-5 h-5 shrink-0" />
                        <div className="flex-1 h-full">
                            <AutocompleteInput
                                value={query}
                                onChange={(val) => {
                                    setLeadScoutState({ query: val })
                                    if (val && bounds) setLeadScoutState({ bounds: null })
                                }}
                                onSearch={() => handleSearch(true)}
                                placeholder="Zip, City, Neighborhood..."
                                className="h-full w-full"
                                inputClassName="bg-transparent border-none focus:ring-0 text-gray-900 dark:text-white placeholder:text-gray-500 h-full w-full focus:outline-none text-base px-0"
                                showIcon={false}
                            />
                        </div>

                        {/* Filter Sheet Trigger */}
                        <Sheet>
                            <SheetTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800">
                                    <SlidersHorizontal className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                                </Button>
                            </SheetTrigger>
                            <SheetContent side="right" className="w-full sm:w-[400px] h-full p-0 bg-gray-950 border-l border-gray-800 text-white">
                                <SheetHeader className="p-4 border-b border-gray-800">
                                    <SheetTitle className="text-white">Search Filters</SheetTitle>
                                </SheetHeader>
                                <ScrollArea className="h-[calc(100vh-80px)]">
                                    <div className="p-4 space-y-6 pb-20">
                                        {/* Limit */}
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium text-gray-400">Results Limit</label>
                                            <Select value={limit.toString()} onValueChange={(val) => setLeadScoutState({ limit: Number(val) })}>
                                                <SelectTrigger className="w-full bg-gray-900 border-gray-800 text-white">
                                                    <SelectValue placeholder="Select limit" />
                                                </SelectTrigger>
                                                <SelectContent className="bg-gray-900 border-gray-800 text-white">
                                                    <SelectItem value="10">10 Leads</SelectItem>
                                                    <SelectItem value="25">25 Leads</SelectItem>
                                                    <SelectItem value="50">50 Leads</SelectItem>
                                                    <SelectItem value="100">100 Leads</SelectItem>
                                                    <SelectItem value="500">500 Leads</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>

                                        {/* Details Toggle */}
                                        <div className="flex items-center justify-between bg-gray-900 p-3 rounded-lg border border-gray-800">
                                            <div className="flex flex-col">
                                                <span className="text-sm font-medium text-white">Fetch Property Details</span>
                                                <span className="text-xs text-gray-500">Includes beds, baths, sqft (Slower)</span>
                                            </div>
                                            <input
                                                type="checkbox"
                                                checked={includePropertyDetails}
                                                onChange={(e) => setIncludePropertyDetails(e.target.checked)}
                                                className="w-5 h-5 rounded border-gray-600 text-green-600 focus:ring-green-500 bg-gray-800"
                                            />
                                        </div>

                                        {/* Filters Component (Reused) */}
                                        <div className="space-y-4">
                                            <LeadFilters
                                                mobile // Pass mobile prop to force expanded view if needed
                                                selectedPropertyTypes={selectedPropertyTypes}
                                                setSelectedPropertyTypes={(val) => setLeadScoutState({ selectedPropertyTypes: val })}
                                                selectedDistressTypes={selectedDistressTypes}
                                                setSelectedDistressTypes={(val) => setLeadScoutState({ selectedDistressTypes: val })}
                                                selectedHotList={selectedHotList}
                                                setSelectedHotList={handleHotListChange}
                                                minBeds={minBeds}
                                                setMinBeds={(val) => setLeadScoutState({ minBeds: val })}
                                                minBaths={minBaths}
                                                setMinBaths={(val) => setLeadScoutState({ minBaths: val })}
                                                minSqft={minSqft}
                                                setMinSqft={(val) => setLeadScoutState({ minSqft: val })}
                                                onSearch={() => { }} // No-op, search is manual
                                            />
                                        </div>
                                    </div>
                                </ScrollArea>
                                <div className="absolute bottom-0 left-0 right-0 p-4 bg-gray-950 border-t border-gray-800">
                                    <SheetClose asChild>
                                        <Button
                                            className="w-full bg-green-600 hover:bg-green-700 text-white h-12 text-lg font-semibold"
                                            onClick={() => query ? handleSearch(true) : handleSearch(false)}
                                        >
                                            Search {limit} Leads
                                        </Button>
                                    </SheetClose>
                                </div>
                            </SheetContent>
                        </Sheet>
                    </div>

                    {/* Bulk Import Button */}
                    {selectedLeadIds.size > 0 && (
                        <Button
                            variant="default"
                            size="sm"
                            onClick={handleBulkImport}
                            className="bg-green-600 hover:bg-green-700 text-white rounded-md h-7 text-xs px-2 shrink-0"
                        >
                            Import ({selectedLeadIds.size})
                        </Button>
                    )}

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

            {/* MAIN CONTENT AREA */}
            <div className="flex-1 relative h-full">

                {/* LIST VIEW - Full Page DataTable */}
                {viewMode === 'list' && (
                    <div className="absolute inset-0 z-20 bg-gray-950 pt-20 overflow-hidden flex flex-col">
                        {/* Table Header */}
                        <div className="px-4 py-3 border-b border-gray-800 flex justify-between items-center bg-gray-900/50 shrink-0">
                            <div className="flex items-center gap-3">
                                <h2 className="font-semibold text-gray-200">RESULTS ({results.length})</h2>
                                {results.length > 0 && (
                                    <div className="flex items-center gap-2 ml-4">
                                        <input
                                            type="checkbox"
                                            id="select-all-table"
                                            className="w-4 h-4 rounded border-gray-600 text-green-600 focus:ring-green-500 bg-gray-700"
                                            checked={results.length > 0 && selectedLeadIds.size === results.length}
                                            onChange={toggleSelectAll}
                                        />
                                        <label htmlFor="select-all-table" className="text-xs text-gray-400 cursor-pointer select-none">
                                            Select All
                                        </label>
                                    </div>
                                )}
                            </div>
                            {/* Mobile Map FAB */}
                            <Button
                                className="md:hidden rounded-full shadow-xl h-10 px-4 bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center gap-2"
                                onClick={() => setLeadScoutState({ viewMode: 'map' })}
                            >
                                <MapIcon className="h-4 w-4" />
                                Map
                            </Button>
                        </div>

                        {/* DataTable with Scroll */}
                        <div className="flex-1 overflow-auto p-4">
                            {results.length > 0 ? (
                                <DataTable columns={scoutColumns} data={results} />
                            ) : (
                                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                                    <ListIcon className="w-12 h-12 mb-4 opacity-50" />
                                    <p className="text-lg">No results yet</p>
                                    <p className="text-sm">Search for leads to see them here</p>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* MAP VIEW - Card Sidebar Overlay (Original) */}
                {viewMode === 'map' && results.length > 0 && (
                    <div className="absolute top-0 bottom-0 right-0 left-16 md:left-auto md:w-[450px] bg-gray-950/95 backdrop-blur-md border-l border-gray-800 z-10 flex pt-16 shadow-2xl flex-col">
                        <div className="p-4 border-b border-gray-800 flex justify-between items-center bg-gray-900/50 backdrop-blur-sm flex-shrink-0">
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
                                <Button variant="ghost" size="sm" onClick={() => setLeadScoutState({ viewMode: 'list' })}>
                                    <ListIcon className="h-4 w-4 mr-2" /> List View
                                </Button>
                            </div>
                        </div>

                        <ScrollArea className="flex-1" ref={listRef}>
                            <div className="p-4 space-y-3">
                                {results.map(lead => (
                                    <Card
                                        key={lead.id}
                                        id={`lead-card-${lead.id}`}
                                        className={`p-3 md:p-4 bg-gray-800/50 border border-gray-700/50 rounded-lg hover:border-green-500/50 transition-all cursor-pointer group relative ${highlightedLeadId === lead.id ? 'ring-2 ring-green-500 bg-gray-800' : ''}`}
                                        onMouseEnter={() => {
                                            setHoveredLeadId(lead.id)
                                            setLeadScoutState({ highlightedLeadId: lead.id })
                                        }}
                                        onMouseLeave={() => {
                                            setHoveredLeadId(null)
                                            setLeadScoutState({ highlightedLeadId: null })
                                        }}
                                        onClick={() => {
                                            setSelectedLead(lead)
                                            setLeadScoutState({ panToLeadId: lead.id })
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

                                        <div className="flex gap-3 pl-8">
                                            {/* Property Thumbnail */}
                                            {(lead as any).primary_photo ? (
                                                <img
                                                    src={(lead as any).primary_photo}
                                                    alt=""
                                                    className="w-16 h-16 object-cover rounded-md border border-gray-600 flex-shrink-0"
                                                />
                                            ) : (
                                                <div className="w-16 h-16 bg-gray-700 rounded-md border border-gray-600 flex items-center justify-center flex-shrink-0">
                                                    <MapIcon className="w-6 h-6 text-gray-500" />
                                                </div>
                                            )}

                                            <div className="flex-1 min-w-0">
                                                <div className="flex justify-between items-start">
                                                    <div className="min-w-0 flex-1">
                                                        <h3 className="font-bold text-white group-hover:text-green-400 transition-colors text-sm truncate">{lead.address}</h3>
                                                        <p className="text-xs text-gray-400">APN: {lead.parcel_id || "Unknown"}</p>
                                                    </div>
                                                    <Button size="icon" variant="ghost" className="h-6 w-6 text-gray-400 hover:text-green-400 flex-shrink-0" onClick={(e) => {
                                                        e.stopPropagation()
                                                        handleImport(lead)
                                                    }}>
                                                        <Download className="w-3 h-3" />
                                                    </Button>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-2 gap-x-4 gap-y-1 mt-3 text-xs text-gray-500 pl-8">
                                            <div className="flex justify-start gap-2">
                                                <span>Est. Value:</span>
                                                <span className="text-white font-mono">
                                                    {lead.estimated_value
                                                        ? `$${lead.estimated_value.toLocaleString()}`
                                                        : lead.arv
                                                            ? `$${lead.arv.toLocaleString()}`
                                                            : "N/A"}
                                                </span>
                                            </div>
                                            <div className="flex justify-start gap-2">
                                                <span>SqFt:</span>
                                                <span className="text-white">{(lead as any).sqft ? (lead as any).sqft.toLocaleString() : "-"}</span>
                                            </div>
                                            <div className="flex justify-start gap-2">
                                                <span>Beds/Baths:</span>
                                                <span className="text-white">{lead.beds || "-"}/{lead.baths || "-"}</span>
                                            </div>
                                        </div>

                                        <div className="flex flex-wrap gap-1 mt-2 pl-8">
                                            {lead.property_type && lead.property_type !== "Unknown" && (
                                                <Badge variant="outline" className="text-[10px] border-gray-700 text-gray-400">
                                                    {lead.property_type}
                                                </Badge>
                                            )}
                                            {lead.distress_signals?.slice(0, 2).map((s, i) => (
                                                <Badge key={i} variant="outline" className="text-[10px] border-red-900 text-red-400 bg-red-950/30">
                                                    {s}
                                                </Badge>
                                            ))}
                                            {(lead.distress_signals?.length ?? 0) > 2 && (
                                                <Badge variant="outline" className="text-[10px] border-red-900 text-red-400 bg-red-950/30">
                                                    +{(lead.distress_signals?.length ?? 0) - 2} more
                                                </Badge>
                                            )}
                                        </div>
                                    </Card>
                                ))}
                            </div>
                        </ScrollArea>
                    </div>
                )}


                {/* MAP BACKGROUND */}
                < div className="absolute inset-0 z-0" >
                    <GoogleScoutMap
                        leads={results}
                        highlightedLeadId={highlightedLeadId}
                        panToLeadId={panToLeadId}
                        onMarkerClick={handleMarkerClick}
                        onMapClick={handleMapClick}
                        onMapSelection={handleMapSelection}
                        onSearchArea={handleSearchArea}
                        selectedBounds={bounds}
                    />
                </div >

                {/* LOADING OVERLAY WITH CANCEL */}
                {
                    loading && (
                        <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-black/40 backdrop-blur-sm">
                            <div className="bg-gray-900 p-6 rounded-xl border border-gray-800 shadow-2xl flex flex-col items-center gap-4">
                                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-green-500"></div>
                                <div className="text-white font-medium">Scouting Leads...</div>
                                <Button
                                    variant="destructive"
                                    size="sm"
                                    onClick={handleCancelSearch}
                                    className="mt-2"
                                >
                                    Cancel Search
                                </Button>
                            </div>
                        </div>
                    )
                }

                {/* "Show List" Toggle Button (Bottom Center) */}
                {
                    viewMode === 'map' && results.length > 0 && (
                        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-50">
                            <Button
                                onClick={() => setLeadScoutState({ viewMode: 'list' })}
                                className="rounded-full shadow-2xl bg-blue-600 hover:bg-blue-700 text-white border-none px-8 py-6 text-lg font-semibold transition-all transform hover:scale-105"
                            >
                                <ListIcon className="w-5 h-5 mr-2" />
                                Show {results.length} Results
                            </Button>
                        </div>
                    )
                }
            </div >

            {/* Detail Dialog */}
            < LeadDetailDialog
                lead={selectedLead}
                open={isDetailOpen}
                onOpenChange={setIsDetailOpen}
                results={results}
                currentIndex={selectedLeadIndex >= 0 ? selectedLeadIndex : undefined}
                onNextLead={handleNextLead}
                onPrevLead={handlePrevLead}
            />
        </div >
    )
}
