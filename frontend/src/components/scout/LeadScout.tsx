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
import { Loader2, Map as MapIcon, List as ListIcon, Download, Search, X, SlidersHorizontal, LayoutGrid, ChevronDown, Check, Zap } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger, SheetClose } from '@/components/ui/sheet'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Filter } from 'lucide-react'
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
        selectedPropertyTypes, selectedPropertySubTypes, selectedDistressTypes,
        selectedHotList, selectedStatuses,
        limit, minBeds, maxBeds, minBaths, maxBaths, minSqft, maxSqft,
        minYearBuilt, maxYearBuilt, hasPool, hasGarage, hasGuestHouse,
        viewMode, highlightedLeadId, panToLeadId, selectedLeadIds,
        bounds
    } = leadScout

    const { toast } = useToast()

    // Local State (UI only)
    const [selectedLead, setSelectedLead] = useState<ScoutResult | null>(null)
    const [isDetailOpen, setIsDetailOpen] = useState(false)
    const [hoveredLeadId, setHoveredLeadId] = useState<string | null>(null)
    const [includePropertyDetails, setIncludePropertyDetails] = useState(false) // Default OFF for fast mode
    const [sidebarOpen, setSidebarOpen] = useState(false) // Right sidebar open/closed state
    const [listFilter, setListFilter] = useState('') // Local filter for DataTable view
    const [filterOpen, setFilterOpen] = useState(false) // Filter dropdown open state
    const [filterSearch, setFilterSearch] = useState('') // Search within filter options

    // Column Filters for DataTable - All filterable columns
    const [columnFilters, setColumnFilters] = useState<{
        // Numeric filters (min/max)
        beds: { min?: number; max?: number; enabled: boolean };
        baths: { min?: number; max?: number; enabled: boolean };
        sqft: { min?: number; max?: number; enabled: boolean };
        year_built: { min?: number; max?: number; enabled: boolean };
        lot_size: { min?: number; max?: number; enabled: boolean };
        stories: { min?: number; max?: number; enabled: boolean };
        assessed_value: { min?: number; max?: number; enabled: boolean };
        // Text filters (multi-select)
        zoning: string[];
        property_type: string[];
        flood_zone: string[];
        neighborhood: string[];
    }>({
        beds: { enabled: false },
        baths: { enabled: false },
        sqft: { enabled: false },
        year_built: { enabled: false },
        lot_size: { enabled: false },
        stories: { enabled: false },
        assessed_value: { enabled: false },
        zoning: [],
        property_type: [],
        flood_zone: [],
        neighborhood: [],
    })


    // Create scout columns with callbacks - includes selection props for checkbox column
    const [analyzingIds, setAnalyzingIds] = useState<Set<string>>(new Set())

    // Handle analyze lead for propensity scoring
    const handleAnalyze = async (lead: ScoutResult) => {
        setAnalyzingIds(prev => new Set(prev).add(lead.id))

        try {
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'
            const res = await fetch(`${baseUrl}/api/v1/scout/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    address: lead.address,
                    owner_name: lead.owner_name,
                    mailing_address: lead.mailing_address,
                    distress_signals: lead.distress_signals || [],
                    violation_count: lead.violation_count || 0,
                    record_date: (lead as any).record_date,
                    seq_num: (lead as any).seq_num,
                    beds: lead.beds,
                    baths: lead.baths,
                })
            })

            if (res.ok) {
                const result = await res.json()
                // Update lead in results with score
                setLeadScoutState({
                    results: results.map(r =>
                        r.id === lead.id
                            ? { ...r, propensity_score: result.score, propensity_label: result.label, propensity_signals: result.signals }
                            : r
                    )
                })
                toast({
                    title: `${result.emoji} Score: ${result.score}`,
                    description: result.action
                })
            } else {
                throw new Error("Analysis failed")
            }
        } catch (error) {
            toast({ title: "Analysis Failed", variant: "destructive" })
        } finally {
            setAnalyzingIds(prev => {
                const newSet = new Set(prev)
                newSet.delete(lead.id)
                return newSet
            })
        }
    }

    // Handle bulk analyze - skips already analyzed leads
    const handleBulkAnalyze = async () => {
        if (selectedLeadIds.size === 0) {
            toast({ title: "No leads selected", variant: "default" })
            return
        }

        // Filter to only unanalyzed leads
        const leadsToAnalyze = results.filter(r =>
            selectedLeadIds.has(r.id) && (r as any).propensity_score === undefined
        )

        if (leadsToAnalyze.length === 0) {
            toast({ title: "All selected leads already analyzed", description: "Select leads without scores to analyze." })
            return
        }

        let successCount = 0
        let skipCount = selectedLeadIds.size - leadsToAnalyze.length

        for (const lead of leadsToAnalyze) {
            await handleAnalyze(lead)
            successCount++
        }

        toast({
            title: `Bulk Analysis Complete`,
            description: `Analyzed ${successCount} leads${skipCount > 0 ? `, skipped ${skipCount} already analyzed` : ''}`
        })

        // Clear selection
        setLeadScoutState({ selectedLeadIds: new Set() })
    }

    const scoutColumns = useMemo(() => createScoutColumns({
        onViewDetails: (lead) => {
            setSelectedLead(lead)
            setIsDetailOpen(true)
            setLeadScoutState({ lastViewedLeadId: lead.id })
        },
        onImport: (lead) => handleImport(lead),
        onAnalyze: (lead) => handleAnalyze(lead),
        analyzingIds,
        // Selection props for checkbox column
        selectedIds: selectedLeadIds,
        onToggleSelect: (id: string) => {
            const newSelected = new Set(selectedLeadIds)
            if (newSelected.has(id)) {
                newSelected.delete(id)
            } else {
                newSelected.add(id)
            }
            setLeadScoutState({ selectedLeadIds: newSelected })
        },
        onToggleAll: () => {
            if (selectedLeadIds.size === results.length) {
                setLeadScoutState({ selectedLeadIds: new Set() })
            } else {
                setLeadScoutState({ selectedLeadIds: new Set(results.map(r => r.id)) })
            }
        },
        allSelected: results.length > 0 && selectedLeadIds.size === results.length
    }), [selectedLeadIds, results, setLeadScoutState, analyzingIds])

    // Compute filtered results for display count and DataTable
    const filteredResults = useMemo(() => {
        return results.filter((r: ScoutResult) => {
            // Text search filter
            if (listFilter) {
                const searchLower = listFilter.toLowerCase()
                const matchesSearch =
                    r.address?.toLowerCase().includes(searchLower) ||
                    r.parcel_id?.toLowerCase().includes(searchLower) ||
                    r.owner_name?.toLowerCase().includes(searchLower) ||
                    r.property_type?.toLowerCase().includes(searchLower) ||
                    r.zoning?.toLowerCase().includes(searchLower)
                if (!matchesSearch) return false
            }

            // Apply column filters
            // Beds filter
            if (columnFilters.beds.enabled) {
                const beds = r.beds ?? 0
                if (columnFilters.beds.min !== undefined && beds < columnFilters.beds.min) return false
                if (columnFilters.beds.max !== undefined && beds > columnFilters.beds.max) return false
            }

            // Baths filter
            if (columnFilters.baths.enabled) {
                const baths = r.baths ?? 0
                if (columnFilters.baths.min !== undefined && baths < columnFilters.baths.min) return false
                if (columnFilters.baths.max !== undefined && baths > columnFilters.baths.max) return false
            }

            // SqFt filter
            if (columnFilters.sqft.enabled) {
                const sqft = r.sqft ?? 0
                if (columnFilters.sqft.min !== undefined && sqft < columnFilters.sqft.min) return false
                if (columnFilters.sqft.max !== undefined && sqft > columnFilters.sqft.max) return false
            }

            // Year Built filter
            if (columnFilters.year_built.enabled) {
                const year = r.year_built ?? 0
                if (columnFilters.year_built.min !== undefined && year < columnFilters.year_built.min) return false
                if (columnFilters.year_built.max !== undefined && year > columnFilters.year_built.max) return false
            }

            // Lot Size filter
            if (columnFilters.lot_size.enabled) {
                const lotSize = (r as any).lot_size ?? 0
                if (columnFilters.lot_size.min !== undefined && lotSize < columnFilters.lot_size.min) return false
                if (columnFilters.lot_size.max !== undefined && lotSize > columnFilters.lot_size.max) return false
            }

            // Stories filter
            if (columnFilters.stories.enabled) {
                const stories = (r as any).stories ?? 0
                if (columnFilters.stories.min !== undefined && stories < columnFilters.stories.min) return false
                if (columnFilters.stories.max !== undefined && stories > columnFilters.stories.max) return false
            }

            // Assessed Value filter
            if (columnFilters.assessed_value.enabled) {
                const value = r.assessed_value ?? 0
                if (columnFilters.assessed_value.min !== undefined && value < columnFilters.assessed_value.min) return false
                if (columnFilters.assessed_value.max !== undefined && value > columnFilters.assessed_value.max) return false
            }

            // Zoning filter (multi-select)
            if (columnFilters.zoning.length > 0) {
                if (!r.zoning || !columnFilters.zoning.includes(r.zoning)) return false
            }

            // Property Type filter (multi-select)
            if (columnFilters.property_type.length > 0) {
                if (!r.property_type || !columnFilters.property_type.includes(r.property_type)) return false
            }

            // Flood Zone filter (multi-select)
            if (columnFilters.flood_zone.length > 0) {
                const floodZone = (r as any).flood_zone
                if (!floodZone || !columnFilters.flood_zone.includes(floodZone)) return false
            }

            // Neighborhood filter (multi-select)
            if (columnFilters.neighborhood.length > 0) {
                const neighborhood = (r as any).neighborhoods
                if (!neighborhood || !columnFilters.neighborhood.includes(neighborhood)) return false
            }

            return true
        })
    }, [results, listFilter, columnFilters])


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
            const payload: any = {
                property_types: selectedPropertyTypes,
                property_subtypes: selectedPropertySubTypes, // Parcel use codes for sub-types
                distress_type: selectedDistressTypes, // Allow empty list for generic search
                hot_list: selectedHotList, // FSBO, Price Reduced, High DOM, New Listing
                listing_statuses: selectedStatuses, // For Sale, Contingent, Pending, etc.
                min_beds: minBeds ? parseInt(minBeds) : undefined,
                max_beds: maxBeds ? parseInt(maxBeds) : undefined,
                min_baths: minBaths ? parseInt(minBaths) : undefined,
                max_baths: maxBaths ? parseInt(maxBaths) : undefined,
                min_sqft: minSqft ? parseInt(minSqft) : undefined,
                max_sqft: maxSqft ? parseInt(maxSqft) : undefined,
                min_year_built: minYearBuilt ? parseInt(minYearBuilt) : undefined,
                max_year_built: maxYearBuilt ? parseInt(maxYearBuilt) : undefined,
                has_pool: hasPool,
                has_garage: hasGarage,
                has_guest_house: hasGuestHouse,
                limit: limit,
                bounds: newBounds, // Include bounds in payload
                // Force HomeHarvest enrichment if searching for specific features that require it (Pool, Garage)
                // Guest House (018x) is from GIS so it doesn't require HomeHarvest
                skip_homeharvest: !includePropertyDetails && !hasPool && !hasGarage
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
                    const KNOWN_CITIES = [
                        "TUCSON", "MARANA", "ORO VALLEY", "VAIL", "SAHUARITA", "SOUTH TUCSON",
                        "CATALINA FOOTHILLS", "CASAS ADOBES", "DREXEL HEIGHTS", "FLOWING WELLS",
                        "TANQUE VERDE", "TUCSON ESTATES", "GREEN VALLEY",
                        "CATALINA", "ORACLE", "SAN MANUEL", "AJO", "SELLS"
                    ]
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
            setSidebarOpen(false) // Ensure sidebar is closed on search results

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
        // Single lead import - uses the bulk API with one lead
        try {
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
            const res = await fetch(`${baseUrl}/api/v1/leads/import`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify([{
                    address: lead.address,
                    address_zip: lead.address_zip,
                    owner_name: lead.owner_name,
                    mailing_address: lead.mailing_address,
                    latitude: lead.latitude,
                    longitude: lead.longitude,
                    bedrooms: lead.beds,
                    bathrooms: lead.baths,
                    sqft: lead.sqft,
                    year_built: lead.year_built,
                    property_type: lead.property_type,
                    parcel_id: lead.parcel_id,
                    zoning: lead.zoning,
                    has_pool: lead.has_pool || false,
                    has_garage: lead.has_garage || false,
                    has_guesthouse: lead.has_guest_house || false,
                    distress_score: lead.distress_score || 0
                }])
            })

            if (res.ok) {
                const result = await res.json()
                if (result.imported > 0) {
                    toast({ title: "Lead Imported", description: `${lead.address} added to Inbox.` })
                } else {
                    toast({ title: "Already in Inbox", description: `${lead.address} was already imported.`, variant: "default" })
                }
            } else {
                throw new Error("Import failed")
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

        setLeadScoutState({ loading: true })

        try {
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

            // Convert selected leads to import format
            const leadsToImport = Array.from(selectedLeadIds)
                .map(id => results.find(r => r.id === id))
                .filter(Boolean)
                .map(lead => ({
                    address: lead!.address,
                    address_zip: lead!.address_zip,
                    owner_name: lead!.owner_name,
                    mailing_address: lead!.mailing_address,
                    latitude: lead!.latitude,
                    longitude: lead!.longitude,
                    bedrooms: lead!.beds,
                    bathrooms: lead!.baths,
                    sqft: lead!.sqft,
                    year_built: lead!.year_built,
                    property_type: lead!.property_type,
                    parcel_id: lead!.parcel_id,
                    zoning: lead!.zoning,
                    has_pool: lead!.has_pool || false,
                    has_garage: lead!.has_garage || false,
                    has_guesthouse: (lead as any).has_guest_house || false,
                    distress_score: lead!.distress_score || 0
                }))

            const res = await fetch(`${baseUrl}/api/v1/leads/import`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(leadsToImport)
            })

            if (res.ok) {
                const result = await res.json()
                setLeadScoutState({ loading: false, selectedLeadIds: new Set() })
                toast({
                    title: "Bulk Import Complete",
                    description: result.message
                })
            } else {
                throw new Error("Bulk import failed")
            }
        } catch (error) {
            setLeadScoutState({ loading: false })
            toast({ title: "Bulk Import Failed", variant: "destructive" })
        }
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
        // Open sidebar and scroll to the clicked property
        setSidebarOpen(true)
        setSelectedLead(lead)
        setIsDetailOpen(true)
        setLeadScoutState({ highlightedLeadId: lead.id, panToLeadId: lead.id, lastViewedLeadId: lead.id })

        // Scroll to item in list
        setTimeout(() => {
            const element = document.getElementById(`lead-card-${lead.id}`)
            if (element) {
                element.scrollIntoView({ behavior: 'smooth', block: 'center' })
            }
        }, 100)
    }

    const handleMapClick = () => {
        // Close sidebar when clicking on empty map area
        setSidebarOpen(false)
        setLeadScoutState({ highlightedLeadId: null, panToLeadId: null })
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
        setLeadScoutState({ selectedHotList: newFilters })

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

    const handleFeatureChange = (key: 'hasPool' | 'hasGarage' | 'hasGuestHouse', val: boolean | null) => {
        setLeadScoutState({ [key]: val })

        // Only Pool and Garage require HomeHarvest details. Guest House is from GIS.
        if (val && !includePropertyDetails && (key === 'hasPool' || key === 'hasGarage')) {
            setIncludePropertyDetails(true)
            toast({
                title: "Details Enabled",
                description: "Pool and Garage filters require detailed property data.",
                duration: 3000
            })
        }

    }

    const handleDetailsToggle = (checked: boolean) => {
        if (checked) {
            setIncludePropertyDetails(true)
            return
        }

        // If disabling, check for dependent filters
        const mlsFilters = ["FSBO", "Price Reduced", "High Days on Market", "New Listing"]
        const hasMlsFilter = selectedHotList.some(f => mlsFilters.includes(f))

        if (hasPool || hasGarage || hasMlsFilter) {
            const confirmDisable = window.confirm(
                "Disabling Property Details will also disable the following active filters:\n\n" +
                (hasPool ? "• Pool\n" : "") +
                (hasGarage ? "• Garage\n" : "") +
                (hasMlsFilter ? "• MLS Filters (FSBO, New Listing, etc.)\n" : "") +
                "\nDo you want to proceed?"
            )

            if (confirmDisable) {
                // User confirmed: Disable details and clear dependent filters
                setIncludePropertyDetails(false)
                setLeadScoutState({
                    hasPool: null,
                    hasGarage: null,
                    selectedHotList: selectedHotList.filter(f => !mlsFilters.includes(f))
                })
            }
            // If cancelled, do nothing (checkbox stays checked)
        } else {
            // No conflicts, just disable
            setIncludePropertyDetails(false)
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

            {/* SEARCH BAR (Floating & Dynamic Position - Only in Map View) */}
            {viewMode !== 'list' && (
                <div className={`absolute top-4 z-50 w-[calc(100%-1rem)] md:w-full max-w-4xl px-0 md:px-4 transition-all duration-300 ease-in-out
                    left-[calc(50%+32px)] md:left-1/2
                    ${sidebarOpen ? 'md:left-[calc(50%-225px+32px)]' : 'md:left-1/2'}
                    -translate-x-1/2 transform pointer-events-none`}>
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
                                selectedPropertySubTypes={selectedPropertySubTypes}
                                setSelectedPropertySubTypes={(val) => setLeadScoutState({ selectedPropertySubTypes: val })}
                                selectedDistressTypes={selectedDistressTypes}
                                setSelectedDistressTypes={(val) => setLeadScoutState({ selectedDistressTypes: val })}
                                selectedHotList={selectedHotList}
                                setSelectedHotList={handleHotListChange}
                                selectedStatuses={selectedStatuses}
                                setSelectedStatuses={(val) => setLeadScoutState({ selectedStatuses: val })}
                                minBeds={minBeds}
                                setMinBeds={(val) => setLeadScoutState({ minBeds: val })}
                                maxBeds={maxBeds}
                                setMaxBeds={(val) => setLeadScoutState({ maxBeds: val })}
                                minBaths={minBaths}
                                setMinBaths={(val) => setLeadScoutState({ minBaths: val })}
                                maxBaths={maxBaths}
                                setMaxBaths={(val) => setLeadScoutState({ maxBaths: val })}
                                minSqft={minSqft}
                                setMinSqft={(val) => setLeadScoutState({ minSqft: val })}
                                maxSqft={maxSqft}
                                setMaxSqft={(val) => setLeadScoutState({ maxSqft: val })}
                                minYearBuilt={minYearBuilt}
                                setMinYearBuilt={(val) => setLeadScoutState({ minYearBuilt: val })}
                                maxYearBuilt={maxYearBuilt}
                                setMaxYearBuilt={(val) => setLeadScoutState({ maxYearBuilt: val })}
                                hasPool={hasPool}
                                setHasPool={(val) => handleFeatureChange('hasPool', val)}
                                hasGarage={hasGarage}
                                setHasGarage={(val) => handleFeatureChange('hasGarage', val)}
                                hasGuestHouse={hasGuestHouse}
                                setHasGuestHouse={(val) => handleFeatureChange('hasGuestHouse', val)}
                                onSearch={() => handleSearch(false)}
                            />
                            <div className="h-4 w-px bg-gray-200 dark:bg-gray-800 mx-1" />
                            <label className="flex items-center gap-1.5 cursor-pointer shrink-0" title="When enabled, fetches detailed property info (beds, baths, sqft, photos) - adds ~45s to search">
                                <input
                                    type="checkbox"
                                    checked={includePropertyDetails}
                                    onChange={(e) => handleDetailsToggle(e.target.checked)}
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
                                                    onChange={(e) => handleDetailsToggle(e.target.checked)}
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
                                                    selectedStatuses={selectedStatuses}
                                                    setSelectedStatuses={(val) => setLeadScoutState({ selectedStatuses: val })}
                                                    minBeds={minBeds}
                                                    setMinBeds={(val) => setLeadScoutState({ minBeds: val })}
                                                    maxBeds={maxBeds}
                                                    setMaxBeds={(val) => setLeadScoutState({ maxBeds: val })}
                                                    minBaths={minBaths}
                                                    setMinBaths={(val) => setLeadScoutState({ minBaths: val })}
                                                    maxBaths={maxBaths}
                                                    setMaxBaths={(val) => setLeadScoutState({ maxBaths: val })}
                                                    minSqft={minSqft}
                                                    setMinSqft={(val) => setLeadScoutState({ minSqft: val })}
                                                    maxSqft={maxSqft}
                                                    setMaxSqft={(val) => setLeadScoutState({ maxSqft: val })}
                                                    minYearBuilt={minYearBuilt}
                                                    setMinYearBuilt={(val) => setLeadScoutState({ minYearBuilt: val })}
                                                    maxYearBuilt={maxYearBuilt}
                                                    setMaxYearBuilt={(val) => setLeadScoutState({ maxYearBuilt: val })}
                                                    hasPool={hasPool}
                                                    setHasPool={(val) => handleFeatureChange('hasPool', val)}
                                                    hasGarage={hasGarage}
                                                    setHasGarage={(val) => handleFeatureChange('hasGarage', val)}
                                                    hasGuestHouse={hasGuestHouse}
                                                    setHasGuestHouse={(val) => handleFeatureChange('hasGuestHouse', val)}
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

                        {/* Bulk Analyze Button */}
                        {selectedLeadIds.size > 0 && (
                            <Button
                                variant="default"
                                size="sm"
                                onClick={handleBulkAnalyze}
                                disabled={analyzingIds.size > 0}
                                className="bg-yellow-600 hover:bg-yellow-700 text-white rounded-md h-7 text-xs px-2 shrink-0"
                            >
                                <Zap className="w-3 h-3 mr-1" />
                                Analyze ({selectedLeadIds.size})
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
            )}

            {/* MAIN CONTENT AREA */}
            <div className="flex-1 relative h-full">

                {/* LIST VIEW - Full Page DataTable */}
                {viewMode === 'list' && (
                    <div className="absolute inset-0 z-20 bg-white dark:bg-gray-950 flex flex-col">
                        {/* Table Header - Results, Select All, Filter, Import */}
                        <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-800 flex items-center justify-center bg-gray-50 dark:bg-gray-900/50 shrink-0 gap-4">
                            {/* Left Side: Results Count, Select All */}
                            <div className="flex items-center gap-4">
                                <h2 className="font-semibold text-gray-800 dark:text-gray-200">
                                    RESULTS ({filteredResults.length !== results.length ? `${filteredResults.length} of ${results.length}` : results.length})
                                </h2>
                                {results.length > 0 && (
                                    <div className="flex items-center gap-2">
                                        <input
                                            type="checkbox"
                                            id="select-all-table"
                                            className="w-4 h-4 rounded border-gray-400 dark:border-gray-600 text-green-600 focus:ring-green-500 bg-white dark:bg-gray-700"
                                            checked={results.length > 0 && selectedLeadIds.size === results.length}
                                            onChange={toggleSelectAll}
                                        />
                                        <label htmlFor="select-all-table" className="text-xs text-gray-600 dark:text-gray-400 cursor-pointer select-none">
                                            Select All
                                        </label>
                                    </div>
                                )}
                            </div>

                            {/* Center: Search Input + Filter Button */}
                            <div className="flex items-center gap-2">
                                <div className="relative w-64">
                                    <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                    <input
                                        type="text"
                                        placeholder="Search results..."
                                        value={listFilter}
                                        onChange={(e) => setListFilter(e.target.value)}
                                        className="w-full h-8 pl-8 pr-3 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-md text-sm text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-1 focus:ring-green-500"
                                    />
                                </div>

                                {/* Filter Panel Button */}
                                <Sheet open={filterOpen} onOpenChange={setFilterOpen}>
                                    <SheetTrigger asChild>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            className={`h-8 gap-1 border-gray-300 dark:border-gray-700 ${Object.values(columnFilters).some(v =>
                                                (typeof v === 'object' && 'enabled' in v && v.enabled) ||
                                                (Array.isArray(v) && v.length > 0)
                                            ) ? 'bg-green-100 dark:bg-green-900/30 border-green-500' : ''
                                                }`}
                                        >
                                            <Filter className="w-4 h-4" />
                                            Filters
                                            {Object.values(columnFilters).filter(v =>
                                                (typeof v === 'object' && 'enabled' in v && v.enabled) ||
                                                (Array.isArray(v) && v.length > 0)
                                            ).length > 0 && (
                                                    <Badge className="ml-1 h-5 w-5 p-0 flex items-center justify-center bg-green-600 text-white text-xs">
                                                        {Object.values(columnFilters).filter(v =>
                                                            (typeof v === 'object' && 'enabled' in v && v.enabled) ||
                                                            (Array.isArray(v) && v.length > 0)
                                                        ).length}
                                                    </Badge>
                                                )}
                                        </Button>
                                    </SheetTrigger>
                                    <SheetContent side="right" className="w-[400px] sm:w-[540px] bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 overflow-y-auto">
                                        <SheetHeader className="pb-4 border-b border-gray-200 dark:border-gray-700">
                                            <div className="flex items-center justify-between">
                                                <SheetTitle className="text-gray-900 dark:text-white">Filters</SheetTitle>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    className="h-7 text-xs text-gray-500 hover:text-gray-900 dark:hover:text-white"
                                                    onClick={() => setColumnFilters({
                                                        beds: { enabled: false },
                                                        baths: { enabled: false },
                                                        sqft: { enabled: false },
                                                        year_built: { enabled: false },
                                                        lot_size: { enabled: false },
                                                        stories: { enabled: false },
                                                        assessed_value: { enabled: false },
                                                        zoning: [],
                                                        property_type: [],
                                                        flood_zone: [],
                                                        neighborhood: [],
                                                    })}
                                                >
                                                    Reset All
                                                </Button>
                                            </div>
                                            {/* Search Filters */}
                                            <div className="relative mt-3">
                                                <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                                <input
                                                    type="text"
                                                    placeholder="Search filters..."
                                                    value={filterSearch}
                                                    onChange={(e) => setFilterSearch(e.target.value)}
                                                    className="w-full h-8 pl-8 pr-3 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md text-sm text-gray-900 dark:text-white placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-green-500"
                                                />
                                            </div>
                                        </SheetHeader>

                                        <div className="py-4 space-y-6">
                                            {/* Quick Filters as Chips */}
                                            <div>
                                                <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Quick Filters</h4>
                                                <div className="flex flex-wrap gap-2">
                                                    {[
                                                        { label: '3+ Beds', key: 'beds', value: { min: 3 } },
                                                        { label: '2+ Baths', key: 'baths', value: { min: 2 } },
                                                        { label: '1500+ SqFt', key: 'sqft', value: { min: 1500 } },
                                                        { label: 'Built after 2000', key: 'year_built', value: { min: 2000 } },
                                                    ].map((quick) => (
                                                        <Badge
                                                            key={quick.label}
                                                            className={`cursor-pointer px-3 py-1 ${(columnFilters[quick.key as keyof typeof columnFilters] as any)?.enabled &&
                                                                (columnFilters[quick.key as keyof typeof columnFilters] as any)?.min === quick.value.min
                                                                ? 'bg-green-600 text-white hover:bg-green-700'
                                                                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                                                                }`}
                                                            onClick={() => {
                                                                const current = columnFilters[quick.key as keyof typeof columnFilters] as any
                                                                if (current?.enabled && current?.min === quick.value.min) {
                                                                    setColumnFilters(prev => ({ ...prev, [quick.key]: { enabled: false } }))
                                                                } else {
                                                                    setColumnFilters(prev => ({ ...prev, [quick.key]: { ...quick.value, enabled: true } }))
                                                                }
                                                            }}
                                                        >
                                                            {quick.label}
                                                        </Badge>
                                                    ))}
                                                </div>
                                            </div>

                                            {/* Property Filters */}
                                            {'property beds baths sqft year stories'.includes(filterSearch.toLowerCase()) && (
                                                <div>
                                                    <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">Property Details</h4>
                                                    <div className="space-y-2">
                                                        {[
                                                            { key: 'beds', label: 'Beds' },
                                                            { key: 'baths', label: 'Baths' },
                                                            { key: 'sqft', label: 'Square Feet' },
                                                            { key: 'year_built', label: 'Year Built' },
                                                            { key: 'lot_size', label: 'Lot Size' },
                                                            { key: 'stories', label: 'Stories' },
                                                        ].filter(f => f.label.toLowerCase().includes(filterSearch.toLowerCase()) || filterSearch === '').map((field) => (
                                                            <div key={field.key} className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3">
                                                                <div className="flex items-center gap-3">
                                                                    <span className="text-sm font-medium text-gray-900 dark:text-white w-24">{field.label}</span>
                                                                    <input
                                                                        type="number"
                                                                        placeholder="Min"
                                                                        value={(columnFilters[field.key as keyof typeof columnFilters] as any)?.min ?? ''}
                                                                        onChange={(e) => {
                                                                            const val = e.target.value ? Number(e.target.value) : undefined
                                                                            setColumnFilters(prev => ({
                                                                                ...prev,
                                                                                [field.key]: {
                                                                                    ...prev[field.key as keyof typeof prev] as any,
                                                                                    min: val,
                                                                                    enabled: val !== undefined || (prev[field.key as keyof typeof prev] as any)?.max !== undefined
                                                                                }
                                                                            }))
                                                                        }}
                                                                        className="flex-1 h-8 px-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded text-sm text-gray-900 dark:text-white"
                                                                    />
                                                                    <span className="text-gray-400 text-sm">-</span>
                                                                    <input
                                                                        type="number"
                                                                        placeholder="Max"
                                                                        value={(columnFilters[field.key as keyof typeof columnFilters] as any)?.max ?? ''}
                                                                        onChange={(e) => {
                                                                            const val = e.target.value ? Number(e.target.value) : undefined
                                                                            setColumnFilters(prev => ({
                                                                                ...prev,
                                                                                [field.key]: {
                                                                                    ...prev[field.key as keyof typeof prev] as any,
                                                                                    max: val,
                                                                                    enabled: val !== undefined || (prev[field.key as keyof typeof prev] as any)?.min !== undefined
                                                                                }
                                                                            }))
                                                                        }}
                                                                        className="flex-1 h-8 px-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded text-sm text-gray-900 dark:text-white"
                                                                    />
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}

                                            {/* Financial Filters */}
                                            {'assessed value financial price'.includes(filterSearch.toLowerCase()) && (
                                                <div>
                                                    <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">Financial</h4>
                                                    <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3">
                                                        <div className="flex items-center gap-3">
                                                            <span className="text-sm font-medium text-gray-900 dark:text-white w-24">Assessed Value</span>
                                                            <input
                                                                type="number"
                                                                placeholder="Min $"
                                                                value={columnFilters.assessed_value.min ?? ''}
                                                                onChange={(e) => {
                                                                    const val = e.target.value ? Number(e.target.value) : undefined
                                                                    setColumnFilters(prev => ({
                                                                        ...prev,
                                                                        assessed_value: {
                                                                            ...prev.assessed_value,
                                                                            min: val,
                                                                            enabled: val !== undefined || prev.assessed_value.max !== undefined
                                                                        }
                                                                    }))
                                                                }}
                                                                className="flex-1 h-8 px-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded text-sm text-gray-900 dark:text-white"
                                                            />
                                                            <span className="text-gray-400 text-sm">-</span>
                                                            <input
                                                                type="number"
                                                                placeholder="Max $"
                                                                value={columnFilters.assessed_value.max ?? ''}
                                                                onChange={(e) => {
                                                                    const val = e.target.value ? Number(e.target.value) : undefined
                                                                    setColumnFilters(prev => ({
                                                                        ...prev,
                                                                        assessed_value: {
                                                                            ...prev.assessed_value,
                                                                            max: val,
                                                                            enabled: val !== undefined || prev.assessed_value.min !== undefined
                                                                        }
                                                                    }))
                                                                }}
                                                                className="flex-1 h-8 px-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded text-sm text-gray-900 dark:text-white"
                                                            />
                                                        </div>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Property Type */}
                                            {'property type'.includes(filterSearch.toLowerCase()) && (
                                                <div>
                                                    <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Property Type</h4>
                                                    <div className="flex flex-wrap gap-2">
                                                        {[...new Set(results.map(r => r.property_type).filter(Boolean))].map((type) => (
                                                            <Badge
                                                                key={type}
                                                                className={`cursor-pointer px-3 py-1 ${columnFilters.property_type.includes(type!)
                                                                    ? 'bg-green-600 text-white hover:bg-green-700'
                                                                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                                                                    }`}
                                                                onClick={() => {
                                                                    if (columnFilters.property_type.includes(type!)) {
                                                                        setColumnFilters(prev => ({ ...prev, property_type: prev.property_type.filter(t => t !== type) }))
                                                                    } else {
                                                                        setColumnFilters(prev => ({ ...prev, property_type: [...prev.property_type, type!] }))
                                                                    }
                                                                }}
                                                            >
                                                                {type}
                                                            </Badge>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}

                                            {/* Zoning */}
                                            {'zoning'.includes(filterSearch.toLowerCase()) && (
                                                <div>
                                                    <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Zoning</h4>
                                                    <div className="flex flex-wrap gap-2">
                                                        {[...new Set(results.map(r => r.zoning).filter(Boolean))].map((zone) => (
                                                            <Badge
                                                                key={zone}
                                                                className={`cursor-pointer px-3 py-1 ${columnFilters.zoning.includes(zone!)
                                                                    ? 'bg-green-600 text-white hover:bg-green-700'
                                                                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                                                                    }`}
                                                                onClick={() => {
                                                                    if (columnFilters.zoning.includes(zone!)) {
                                                                        setColumnFilters(prev => ({ ...prev, zoning: prev.zoning.filter(z => z !== zone) }))
                                                                    } else {
                                                                        setColumnFilters(prev => ({ ...prev, zoning: [...prev.zoning, zone!] }))
                                                                    }
                                                                }}
                                                            >
                                                                {zone}
                                                            </Badge>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}

                                            {/* Flood Zone */}
                                            {'flood zone'.includes(filterSearch.toLowerCase()) && (
                                                <div>
                                                    <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Flood Zone</h4>
                                                    <div className="flex flex-wrap gap-2">
                                                        {[...new Set(results.map(r => (r as any).flood_zone).filter(Boolean))].map((zone: string) => (
                                                            <Badge
                                                                key={zone}
                                                                className={`cursor-pointer px-3 py-1 ${columnFilters.flood_zone.includes(zone)
                                                                    ? 'bg-green-600 text-white hover:bg-green-700'
                                                                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                                                                    }`}
                                                                onClick={() => {
                                                                    if (columnFilters.flood_zone.includes(zone)) {
                                                                        setColumnFilters(prev => ({ ...prev, flood_zone: prev.flood_zone.filter(z => z !== zone) }))
                                                                    } else {
                                                                        setColumnFilters(prev => ({ ...prev, flood_zone: [...prev.flood_zone, zone] }))
                                                                    }
                                                                }}
                                                            >
                                                                {zone}
                                                            </Badge>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </SheetContent>
                                </Sheet>
                            </div>

                            {/* Right Side: Import Button */}
                            {selectedLeadIds.size > 0 && (
                                <Button
                                    size="sm"
                                    className="h-8 bg-green-600 hover:bg-green-700 text-white"
                                    onClick={handleBulkImport}
                                >
                                    <Download className="w-4 h-4 mr-1" />
                                    Import {selectedLeadIds.size}
                                </Button>
                            )}

                            {/* Right Side: Bulk Analyze Button */}
                            {selectedLeadIds.size > 0 && (
                                <Button
                                    size="sm"
                                    className="h-8 bg-yellow-600 hover:bg-yellow-700 text-white"
                                    onClick={handleBulkAnalyze}
                                    disabled={analyzingIds.size > 0}
                                >
                                    <Zap className="w-4 h-4 mr-1" />
                                    Analyze {selectedLeadIds.size}
                                </Button>
                            )}
                        </div>


                        {/* DataTable with Scroll - full height, no bottom padding */}
                        <div className="flex-1 overflow-auto px-4">
                            {results.length > 0 ? (
                                <DataTable
                                    columns={scoutColumns}
                                    data={filteredResults}
                                    onRowClick={(row) => {
                                        setSelectedLead(row as ScoutResult)
                                        setLeadScoutState({ highlightedLeadId: (row as ScoutResult).id, lastViewedLeadId: (row as ScoutResult).id })
                                        setIsDetailOpen(true)
                                    }}
                                />
                            ) : (
                                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                                    <ListIcon className="w-12 h-12 mb-4 opacity-50" />
                                    <p className="text-lg">No results yet</p>
                                    <p className="text-sm">Search for leads to see them here</p>
                                </div>
                            )}
                        </div>

                        {/* Map View Button - Bottom Center */}
                        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-30">
                            <Button
                                onClick={() => setLeadScoutState({ viewMode: 'map' })}
                                className="rounded-full shadow-2xl bg-blue-600 hover:bg-blue-700 text-white px-6 py-5 text-base font-semibold"
                            >
                                <MapIcon className="w-5 h-5 mr-2" />
                                Map View
                            </Button>
                        </div>
                    </div>
                )}


                {/* PROPERTY SIDEBAR (Right Panel) */}
                {sidebarOpen && results.length > 0 && (
                    <div className="absolute top-0 bottom-0 right-0 left-0 md:left-auto md:w-[450px] bg-gray-950/95 backdrop-blur-md border-l border-gray-800 z-10 flex pt-16 shadow-2xl flex-col">
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
                            {/* List/Map Toggle */}
                            <Tabs value={sidebarOpen ? 'list' : 'map'} onValueChange={(v) => setSidebarOpen(v === 'list')} className="shrink-0">
                                <TabsList className="h-8 bg-gray-800 p-0.5">
                                    <TabsTrigger value="list" className="h-7 px-3 text-xs data-[state=active]:bg-gray-700 data-[state=active]:text-white">
                                        <ListIcon className="w-3.5 h-3.5 mr-1" />
                                        List
                                    </TabsTrigger>
                                    <TabsTrigger value="map" className="h-7 px-3 text-xs data-[state=active]:bg-gray-700 data-[state=active]:text-white">
                                        <MapIcon className="w-3.5 h-3.5 mr-1" />
                                        Map
                                    </TabsTrigger>
                                </TabsList>
                            </Tabs>
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
                                            setLeadScoutState({ panToLeadId: lead.id, lastViewedLeadId: lead.id })
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
                                            {(lead as any).has_pool && (
                                                <Badge variant="outline" className="text-[10px] border-blue-900 text-blue-400 bg-blue-950/30">
                                                    Pool
                                                </Badge>
                                            )}
                                            {(lead as any).has_garage && (
                                                <Badge variant="outline" className="text-[10px] border-gray-600 text-gray-300 bg-gray-800/30">
                                                    Garage
                                                </Badge>
                                            )}
                                            {(lead as any).has_guest_house && (
                                                <Badge variant="outline" className="text-[10px] border-purple-900 text-purple-400 bg-purple-950/30">
                                                    Guest House
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
                        highlightedLeadId={highlightedLeadId || leadScout.lastViewedLeadId}
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

                {/* Bottom Center Button - Show Results (map view) or Map (list view) */}
                {results.length > 0 && viewMode !== 'list' && (
                    <div className={`absolute bottom-8 z-50 transition-all duration-300
                        left-[calc(50%+32px)] md:left-1/2
                        ${sidebarOpen ? 'md:left-[calc(50%-225px+32px)]' : 'md:left-1/2'}
                        -translate-x-1/2`}>
                        <Button
                            onClick={() => setLeadScoutState({ viewMode: 'list' })}
                            className="rounded-full shadow-2xl bg-green-600 hover:bg-green-700 text-white border-none px-8 py-6 text-lg font-semibold transition-all transform hover:scale-105"
                        >
                            <ListIcon className="w-5 h-5 mr-2" />
                            Show {results.length} Results
                        </Button>
                    </div>
                )}

            </div >

            {/* Detail Dialog */}
            <LeadDetailDialog
                lead={selectedLead}
                open={isDetailOpen}
                onOpenChange={(open) => {
                    setIsDetailOpen(open)
                    // When closing, ensure the map highlights and pans to the last viewed lead
                    if (!open && selectedLead) {
                        setLeadScoutState({
                            highlightedLeadId: selectedLead.id,
                            panToLeadId: selectedLead.id
                        })
                    }
                }}
                results={results}
                currentIndex={selectedLeadIndex >= 0 ? selectedLeadIndex : undefined}
                onNextLead={handleNextLead}
                onPrevLead={handlePrevLead}
                onSwitchToListView={() => setLeadScoutState({ viewMode: 'list' })}
                onSwitchToMapView={() => {
                    // Switch to map and highlight/pan to the current property
                    setLeadScoutState({
                        viewMode: 'map',
                        highlightedLeadId: selectedLead?.id || null,
                        panToLeadId: selectedLead?.id || null
                    })
                    setSidebarOpen(false) // Close sidebar to show full map
                }}
                currentViewMode={viewMode}
            />

        </div >
    )
}
