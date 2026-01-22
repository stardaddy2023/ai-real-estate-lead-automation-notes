import React, { useState, useEffect, useCallback } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { ScoutResult } from '@/lib/store'
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { User, Phone, Mail, Building2, DollarSign, AlertTriangle, Gavel, FileText, MapPin, Droplets, TrendingUp, Home, Calendar, Ruler, ChevronLeft, ChevronRight, List as ListIcon, Map as MapIcon, Zap, Loader2, Search, Download } from 'lucide-react'
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/simple-accordion"

// Analysis state type
interface AnalysisResult {
    score: number
    label: string
    emoji: string
    signals: string[]
    breakdown: { motivation: number; equity: number; asset: number }
    action: string
}

// Recording document from Recorder search
interface RecordingDocument {
    doc_id: string
    doc_number: string
    doc_type: string
    record_date: string
}

// Module-level cache for recorder results (persists between property switches)
// Keyed by owner_name to avoid re-fetching when switching between same properties
const recorderCache = new Map<string, RecordingDocument[]>()

interface LeadDetailDialogProps {
    lead: ScoutResult | null
    open: boolean
    onOpenChange: (open: boolean) => void
    // New props for lead navigation
    results?: ScoutResult[]
    onNextLead?: () => void
    onPrevLead?: () => void
    currentIndex?: number
    // View toggle
    onSwitchToListView?: () => void
    onSwitchToMapView?: () => void
    currentViewMode?: 'list' | 'map'
}

// Helper to format currency
const formatCurrency = (value: number | undefined | null) => {
    if (!value && value !== 0) return "N/A"
    return `$${value?.toLocaleString()}`
}

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

// Helper to parse alt_photos string into array
const parseAltPhotos = (altPhotos: string | undefined): string[] => {
    if (!altPhotos) return []
    // alt_photos can be comma-separated or a single URL
    return altPhotos.split(',').map(url => url.trim()).filter(url => url.length > 0)
}

export function LeadDetailDialog({ lead, open, onOpenChange, results, onNextLead, onPrevLead, currentIndex, onSwitchToListView, onSwitchToMapView, currentViewMode }: LeadDetailDialogProps) {
    const [currentImageIndex, setCurrentImageIndex] = useState(0)
    const [isAnalyzing, setIsAnalyzing] = useState(false)
    const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
    const [isLoadingRecordings, setIsLoadingRecordings] = useState(false)
    const [recordingHistory, setRecordingHistory] = useState<RecordingDocument[]>([])
    const [recordingError, setRecordingError] = useState<string | null>(null)

    // Reset image index and analysis when lead changes, but restore cached recorder results
    useEffect(() => {
        setCurrentImageIndex(0)
        setAnalysisResult(null)
        setRecordingError(null)

        // Check if we have cached recorder results for this owner
        if (lead?.owner_name && recorderCache.has(lead.owner_name)) {
            setRecordingHistory(recorderCache.get(lead.owner_name) || [])
        } else {
            setRecordingHistory([])
        }
    }, [lead?.id])

    if (!lead) return null

    // Access GIS properties via type assertion
    const extLead = lead as ScoutResult & {
        zoning?: string
        municipality?: string
        flood_zone?: string
        school_district?: string
        nearby_development?: string
        development_status?: string
        violations?: Array<{ description: string; activity_num: string }>
        phone?: string
        email?: string
        // Property features
        has_pool?: boolean
        has_garage?: boolean
        has_guest_house?: boolean
        garage_spaces?: number
        // HomeHarvest/MLS fields
        half_baths?: number
        stories?: number
        neighborhoods?: string
        subdivision?: string
        hoa_fee?: number
        price_per_sqft?: number
        description?: string
        listing_description?: string  // MLS listing description
        status?: string  // Listing status (Active, Pending, etc.)
        mls_source?: string  // Data source (Realtor.com, Zillow, etc.)
        days_on_market?: number
        list_price?: number
        list_date?: string
        agent_name?: string
        office_name?: string
        last_sold_price?: number
        last_sold_date?: string
        primary_photo?: string
        alt_photos?: string
        property_url?: string
        estimated_value?: number
        lot_sqft?: number
        parking_garage?: string
        assessor_url?: string
        source?: string  // homeharvest_mls or gis
        mls_id?: string  // MLS listing ID for display
        // Recording/Deed Info from GIS
        seq_num?: string
        docket?: string
        page?: number
        record_date?: string | number
        // Propensity Analysis
        propensity_score?: number
        propensity_label?: string
        propensity_emoji?: string
        propensity_signals?: string[]
        propensity_breakdown?: { motivation: number; equity: number; asset: number }
        propensity_action?: string
    }

    // Check if this is an MLS listing (has listing-specific data)
    const isMLSListing = extLead.source === "homeharvest_mls" || extLead.mls_source || extLead.list_price

    // Check if location section has data
    const hasLocationData = extLead.zoning || extLead.flood_zone || extLead.school_district || extLead.nearby_development

    // Build images array from primary_photo and alt_photos
    const altPhotosArray = parseAltPhotos(extLead.alt_photos)
    const allImages = extLead.primary_photo
        ? [extLead.primary_photo, ...altPhotosArray]
        : altPhotosArray
    const hasMultipleImages = allImages.length > 1

    // Image navigation handlers
    const goToNextImage = () => {
        if (allImages.length > 0) {
            setCurrentImageIndex((prev) => (prev + 1) % allImages.length)
        }
    }
    const goToPrevImage = () => {
        if (allImages.length > 0) {
            setCurrentImageIndex((prev) => (prev - 1 + allImages.length) % allImages.length)
        }
    }

    // Lead navigation enabled check
    const canNavigateLeads = results && results.length > 1
    const canGoPrev = canNavigateLeads && currentIndex !== undefined && currentIndex > 0
    const canGoNext = canNavigateLeads && currentIndex !== undefined && currentIndex < results.length - 1

    // Handle Analyze button click
    const handleAnalyze = async () => {
        if (!lead || isAnalyzing) return

        setIsAnalyzing(true)
        try {
            const response = await fetch('http://127.0.0.1:8000/api/v1/scout/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    address: lead.address,
                    owner_name: lead.owner_name,
                    mailing_address: lead.mailing_address,
                    distress_signals: lead.distress_signals || [],
                    violation_count: (lead as any).violation_count || 0,
                    record_date: extLead.record_date,
                    seq_num: extLead.seq_num,
                    beds: lead.beds,
                    baths: lead.baths,
                })
            })
            const data = await response.json()
            setAnalysisResult(data)
        } catch (error) {
            console.error('Analysis failed:', error)
        } finally {
            setIsAnalyzing(false)
        }
    }

    // Handle Recording History Lookup
    const handleLookupRecordings = async () => {
        if (!lead?.owner_name || isLoadingRecordings) return

        setIsLoadingRecordings(true)
        setRecordingError(null)
        try {
            // Search by owner name as BOTH grantor (seller) and grantee (buyer) to find all their documents
            const response = await fetch(`http://127.0.0.1:8000/api/v1/recorder/search/name/${encodeURIComponent(lead.owner_name)}?search_type=both&deed_only=false&limit=20`)
            if (!response.ok) {
                // Check for 503 (session not active)
                if (response.status === 503) {
                    const errorData = await response.json().catch(() => null)
                    setRecordingError(errorData?.detail || 'Recorder session not active. Open the Recorder page first.')
                    return
                }
                throw new Error('Failed to search recorder')
            }
            const data = await response.json()
            if (data.results && data.results.length > 0) {
                setRecordingHistory(data.results)
                // Cache results by owner name for persistence
                recorderCache.set(lead.owner_name, data.results)
            } else {
                setRecordingError('No deed records found for this owner')
            }
        } catch (error) {
            console.error('Recording lookup failed:', error)
            setRecordingError('Recorder search failed. Please try again.')
        } finally {
            setIsLoadingRecordings(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto bg-gradient-to-br from-gray-900 to-gray-950 border-gray-700">
                {/* Lead Navigation Bar */}
                {canNavigateLeads && (
                    <div className="flex items-center justify-between py-2 px-1 border-b border-gray-800 mb-2">
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={onPrevLead}
                            disabled={!canGoPrev}
                            className="text-gray-400 hover:text-white disabled:opacity-30"
                        >
                            <ChevronLeft className="h-4 w-4 mr-1" />
                            Previous
                        </Button>
                        <span className="text-xs text-gray-500">
                            {(currentIndex ?? 0) + 1} of {results?.length ?? 0}
                        </span>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={onNextLead}
                            disabled={!canGoNext}
                            className="text-gray-400 hover:text-white disabled:opacity-30"
                        >
                            Next
                            <ChevronRight className="h-4 w-4 ml-1" />
                        </Button>
                    </div>
                )}

                {/* Image Carousel */}
                {allImages.length > 0 && (
                    <div className="mb-4 flex flex-col items-center">
                        {/* Main Image */}
                        <div className="relative w-full max-w-lg aspect-[4/3] bg-gray-800 rounded-lg overflow-hidden">
                            <img
                                src={allImages[currentImageIndex]}
                                alt={`${lead.address} - Photo ${currentImageIndex + 1}`}
                                className="w-full h-full object-contain"
                            />
                            {/* Navigation Arrows */}
                            {hasMultipleImages && (
                                <>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        onClick={goToPrevImage}
                                        className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white rounded-full h-10 w-10"
                                    >
                                        <ChevronLeft className="h-6 w-6" />
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        onClick={goToNextImage}
                                        className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white rounded-full h-10 w-10"
                                    >
                                        <ChevronRight className="h-6 w-6" />
                                    </Button>
                                </>
                            )}
                            {/* Image Counter */}
                            <div className="absolute bottom-2 right-2 bg-black/60 text-white text-xs px-2 py-1 rounded">
                                {currentImageIndex + 1} / {allImages.length}
                            </div>
                        </div>
                        {/* Thumbnail Grid */}
                        {hasMultipleImages && (
                            <div className="w-full max-w-lg mt-2 max-h-28 overflow-y-auto">
                                <div className="grid grid-cols-8 gap-1">
                                    {allImages.map((img, idx) => (
                                        <button
                                            key={idx}
                                            onClick={() => setCurrentImageIndex(idx)}
                                            className={`aspect-square rounded overflow-hidden border-2 transition-all ${idx === currentImageIndex
                                                ? 'border-green-500 ring-1 ring-green-500/50'
                                                : 'border-gray-600 hover:border-gray-400'
                                                }`}
                                        >
                                            <img src={img} alt={`Thumbnail ${idx + 1}`} className="w-full h-full object-cover" />
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Header */}
                <DialogHeader className="pb-4 border-b border-gray-700">
                    <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                            <DialogTitle className="text-xl font-bold text-white flex items-center gap-3 flex-wrap">
                                <Home className="h-5 w-5 text-green-400" />
                                {lead.address}
                            </DialogTitle>
                            <p className="text-sm text-gray-400 mt-1">
                                APN: {lead.parcel_id || "Unknown"}
                                {isMLSListing && extLead.mls_id && <span className="ml-3 text-gray-500">| MLS ID: {extLead.mls_id}</span>}
                            </p>
                            {extLead.neighborhoods && (
                                <p className="text-xs text-gray-500 mt-1">{extLead.neighborhoods}</p>
                            )}
                        </div>
                        <div className="flex flex-wrap gap-1 max-w-[200px]">
                            {extLead.status && extLead.status !== "Active" && (
                                <Badge className={`text-xs ${extLead.status.toLowerCase().includes('pending') || extLead.status.toLowerCase().includes('contingent') ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50' : 'bg-blue-500/20 text-blue-400 border-blue-500/50'}`}>
                                    {extLead.status}
                                </Badge>
                            )}
                            {extLead.mls_source && (
                                <Badge className="bg-green-500/20 text-green-400 border-green-500/50 text-xs">
                                    {extLead.mls_source}
                                </Badge>
                            )}
                            {lead.distress_signals?.slice(0, 3).map((signal, i) => (
                                <Badge key={i} className="bg-red-500/20 text-red-400 border-red-500/50 text-xs">
                                    {signal}
                                </Badge>
                            ))}
                            {/* Analyze Button */}
                            <Button
                                size="sm"
                                variant="outline"
                                onClick={handleAnalyze}
                                disabled={isAnalyzing}
                                className={`ml-2 border-yellow-500/50 text-yellow-400 hover:bg-yellow-500/20 ${analysisResult ? 'bg-yellow-500/10' : ''}`}
                            >
                                {isAnalyzing ? (
                                    <Loader2 className="h-3 w-3 animate-spin mr-1" />
                                ) : (
                                    <Zap className="h-3 w-3 mr-1" />
                                )}
                                {analysisResult ? `${analysisResult.emoji} ${analysisResult.score}` : 'Analyze'}
                            </Button>
                        </div>
                    </div>
                </DialogHeader>

                {/* Propensity Analysis Results (shown after analysis) */}
                {analysisResult && (
                    <div className="mb-4 p-4 bg-gradient-to-r from-yellow-900/20 to-orange-900/20 border border-yellow-500/30 rounded-lg">
                        <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                                <span className="text-2xl">{analysisResult.emoji}</span>
                                <div>
                                    <span className="text-lg font-bold text-white">{analysisResult.score}</span>
                                    <span className="text-sm text-gray-400 ml-2">/ 100</span>
                                    <Badge className={`ml-2 ${analysisResult.label === 'Hot' ? 'bg-green-500/20 text-green-400' :
                                        analysisResult.label === 'Warm' ? 'bg-yellow-500/20 text-yellow-400' :
                                            'bg-gray-500/20 text-gray-400'
                                        }`}>{analysisResult.label}</Badge>
                                </div>
                            </div>
                            <p className="text-sm text-gray-400">{analysisResult.action}</p>
                        </div>

                        {/* Score Breakdown */}
                        <div className="grid grid-cols-3 gap-2 mb-3">
                            <div className="p-2 bg-gray-800/50 rounded text-center">
                                <p className="text-xs text-gray-400">Motivation</p>
                                <p className="text-lg font-bold text-red-400">+{analysisResult.breakdown.motivation}</p>
                            </div>
                            <div className="p-2 bg-gray-800/50 rounded text-center">
                                <p className="text-xs text-gray-400">Equity</p>
                                <p className="text-lg font-bold text-green-400">{analysisResult.breakdown.equity >= 0 ? '+' : ''}{analysisResult.breakdown.equity}</p>
                            </div>
                            <div className="p-2 bg-gray-800/50 rounded text-center">
                                <p className="text-xs text-gray-400">Asset</p>
                                <p className="text-lg font-bold text-blue-400">+{analysisResult.breakdown.asset}</p>
                            </div>
                        </div>

                        {/* Detected Signals */}
                        {analysisResult.signals.length > 0 && (
                            <div>
                                <p className="text-xs text-gray-500 mb-2">Detected Signals</p>
                                <div className="flex flex-wrap gap-1">
                                    {analysisResult.signals.map((signal, idx) => (
                                        <Badge key={idx} className="bg-gray-700/50 text-gray-300 text-xs">
                                            {signal}
                                        </Badge>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Quick Stats Bar */}
                <div className="grid grid-cols-5 gap-2 py-4 border-b border-gray-700">
                    <div className="text-center">
                        <div className="text-2xl font-bold text-white">{lead.beds || "—"}</div>
                        <div className="text-xs text-gray-400">Beds</div>
                    </div>
                    <div className="text-center">
                        <div className="text-xl font-bold text-white">
                            {lead.baths || "—"}{extLead.half_baths ? <span className="text-sm text-gray-400">/{extLead.half_baths}</span> : ""}
                        </div>
                        <div className="text-xs text-gray-400">Full/Half</div>
                    </div>
                    <div className="text-center">
                        <div className="text-2xl font-bold text-white">{lead.sqft ? lead.sqft.toLocaleString() : "—"}</div>
                        <div className="text-xs text-gray-400">Sqft</div>
                    </div>
                    <div className="text-center">
                        <div className="text-xl font-bold text-white">{extLead.stories || "—"}</div>
                        <div className="text-xs text-gray-400">Stories</div>
                    </div>
                    <div className="text-center">
                        <div className="text-lg font-bold text-green-400">{formatCurrency(extLead.estimated_value || lead.assessed_value)}</div>
                        <div className="text-xs text-gray-400">{extLead.estimated_value ? "Est. Value" : "Assessed"}</div>
                    </div>
                </div>

                <Accordion type="multiple" defaultValue={["listing", "property", "recorder", "contact", "financials", "distress"]} className="w-full mt-2">

                    {/* Listing Details (MLS Only) */}
                    {isMLSListing && (
                        <AccordionItem value="listing" className="border-gray-700">
                            <AccordionTrigger className="text-white hover:text-green-400">
                                <div className="flex items-center gap-2">
                                    <DollarSign className="h-4 w-4 text-green-400" />
                                    Listing Details
                                    {extLead.mls_source && (
                                        <Badge className="ml-2 bg-green-500/20 text-green-400 text-[10px]">{extLead.mls_source}</Badge>
                                    )}
                                </div>
                            </AccordionTrigger>
                            <AccordionContent>
                                {/* Price & Market Row */}
                                <div className="grid grid-cols-3 gap-3 text-sm mb-3">
                                    <div className="p-3 bg-green-900/20 border border-green-500/30 rounded-lg text-center">
                                        <p className="text-xs text-gray-400 mb-1">Asking Price</p>
                                        <p className="text-xl font-bold text-green-400">{formatCurrency(extLead.list_price)}</p>
                                    </div>
                                    <div className="p-3 bg-gray-800/50 rounded-lg text-center">
                                        <p className="text-xs text-gray-400 mb-1">Days on Market</p>
                                        <p className="text-xl font-bold text-white">{extLead.days_on_market ?? "—"}</p>
                                    </div>
                                    <div className="p-3 bg-gray-800/50 rounded-lg text-center">
                                        <p className="text-xs text-gray-400 mb-1">Price/SqFt</p>
                                        <p className="text-xl font-bold text-white">{extLead.price_per_sqft ? `$${extLead.price_per_sqft}` : "—"}</p>
                                    </div>
                                </div>

                                {/* Listing Info Row */}
                                <div className="grid grid-cols-2 gap-3 text-sm mb-3">
                                    <div className="p-3 bg-gray-800/50 rounded-lg">
                                        <p className="text-xs text-gray-400">List Date</p>
                                        <p className="font-medium text-white">{extLead.list_date ? new Date(extLead.list_date).toLocaleDateString() : "N/A"}</p>
                                    </div>
                                    <div className="p-3 bg-gray-800/50 rounded-lg">
                                        <p className="text-xs text-gray-400">HOA Fee</p>
                                        <p className="font-medium text-white">{extLead.hoa_fee !== undefined && extLead.hoa_fee !== null ? (extLead.hoa_fee === 0 ? "None" : `$${extLead.hoa_fee}/mo`) : "N/A"}</p>
                                    </div>
                                    <div className="p-3 bg-gray-800/50 rounded-lg">
                                        <p className="text-xs text-gray-400">Last Sold</p>
                                        <p className="font-medium text-white">{extLead.last_sold_date ? new Date(extLead.last_sold_date).toLocaleDateString() : "N/A"}</p>
                                    </div>
                                    <div className="p-3 bg-gray-800/50 rounded-lg">
                                        <p className="text-xs text-gray-400">Last Sold Price</p>
                                        <p className="font-medium text-white">{formatCurrency(extLead.last_sold_price)}</p>
                                    </div>
                                </div>

                                {/* Agent Info Row */}
                                <div className="grid grid-cols-2 gap-3 text-sm mb-3">
                                    <div className="p-3 bg-gray-800/50 rounded-lg">
                                        <p className="text-xs text-gray-400">Listing Agent</p>
                                        <p className="font-medium text-white truncate">{extLead.agent_name || "N/A"}</p>
                                    </div>
                                    <div className="p-3 bg-gray-800/50 rounded-lg">
                                        <p className="text-xs text-gray-400">Brokerage</p>
                                        <p className="font-medium text-white truncate">{extLead.office_name || "N/A"}</p>
                                    </div>
                                </div>

                                {/* Listing Description */}
                                {extLead.listing_description && (
                                    <div className="mt-3 pt-3 border-t border-gray-700">
                                        <p className="text-xs text-gray-500 mb-2 flex items-center justify-center gap-1">
                                            <FileText className="h-3 w-3" /> Listing Description
                                        </p>
                                        <div className="p-3 bg-gray-800/50 rounded-lg">
                                            <p className="text-sm text-gray-300 leading-relaxed text-center">
                                                {extLead.listing_description}
                                            </p>
                                        </div>
                                    </div>
                                )}

                                {/* View Listing Link */}
                                {extLead.assessor_url && (
                                    <div className="mt-3 pt-3 border-t border-gray-700">
                                        <a href={extLead.assessor_url} target="_blank" rel="noopener noreferrer" className="flex items-center justify-center w-full p-2 bg-green-900/20 border border-green-500/30 rounded-lg text-green-400 hover:bg-green-900/40 transition-colors text-sm gap-2">
                                            <FileText className="h-4 w-4" />
                                            View Original Listing
                                        </a>
                                    </div>
                                )}
                            </AccordionContent>
                        </AccordionItem>
                    )}

                    {/* Property Details & Location (Combined) */}
                    <AccordionItem value="property" className="border-gray-700">
                        <AccordionTrigger className="text-white hover:text-green-400">
                            <div className="flex items-center gap-2">
                                <Building2 className="h-4 w-4 text-blue-400" />
                                Property Details
                                {hasLocationData && (
                                    <Badge className="ml-2 bg-green-500/20 text-green-400 text-[10px]">GIS Data</Badge>
                                )}
                            </div>
                        </AccordionTrigger>
                        <AccordionContent>
                            {/* Property Info Row */}
                            <div className="grid grid-cols-2 gap-3 text-sm">
                                <div className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg">
                                    <Home className="h-4 w-4 text-gray-400" />
                                    <div>
                                        <p className="text-xs text-gray-400">Property Type</p>
                                        <p className="font-medium text-white">{lead.property_type || "Unknown"}</p>
                                        {(lead as any).parcel_use_code && (
                                            <p className="text-xs text-gray-500">Code: {(lead as any).parcel_use_code}</p>
                                        )}
                                    </div>
                                </div>
                                <div className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg">
                                    <Calendar className="h-4 w-4 text-gray-400" />
                                    <div>
                                        <p className="text-xs text-gray-400">Year Built</p>
                                        <p className="font-medium text-white">{lead.year_built || "N/A"}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg">
                                    <Ruler className="h-4 w-4 text-gray-400" />
                                    <div>
                                        <p className="text-xs text-gray-400">Lot Size</p>
                                        <p className="font-medium text-white">{lead.lot_size ? `${lead.lot_size.toLocaleString()} sqft` : "N/A"}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg">
                                    <Building2 className="h-4 w-4 text-gray-400" />
                                    <div>
                                        <p className="text-xs text-gray-400">Living Sqft</p>
                                        <p className="font-medium text-white">{lead.sqft ? `${lead.sqft.toLocaleString()} sqft` : "N/A"}</p>
                                    </div>
                                </div>

                                {/* Property Features (Pool, Garage, Guest House) */}
                                {(extLead.has_pool || extLead.has_garage || extLead.has_guest_house) && (
                                    <div className="mt-3 pt-3 border-t border-gray-700">
                                        <p className="text-xs text-gray-500 mb-2">Property Features</p>
                                        <div className="flex flex-wrap gap-2">
                                            {extLead.has_pool && (
                                                <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/50">
                                                    🏊 Pool
                                                </Badge>
                                            )}
                                            {extLead.has_garage && (
                                                <Badge className="bg-gray-500/20 text-gray-300 border-gray-500/50">
                                                    🚗 Garage {extLead.garage_spaces ? `(${extLead.garage_spaces})` : ""}
                                                </Badge>
                                            )}
                                            {extLead.has_guest_house && (
                                                <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/50">
                                                    🏠 Guest House
                                                </Badge>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* Assessor Link - only show for non-MLS leads (MLS has "View Original Listing" in Listing Details) */}
                                {extLead.assessor_url && !isMLSListing && (
                                    <div className="mt-3 pt-3 border-t border-gray-700">
                                        <a href={extLead.assessor_url} target="_blank" rel="noopener noreferrer" className="flex items-center justify-center w-full p-2 bg-blue-900/20 border border-blue-500/30 rounded-lg text-blue-400 hover:bg-blue-900/40 transition-colors text-sm gap-2">
                                            <FileText className="h-4 w-4" />
                                            View Official Assessor Record
                                        </a>
                                    </div>
                                )}

                                {/* Recording Info Section - Always show with lookup button */}
                                <div className="mt-3 pt-3 border-t border-gray-700">
                                    <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">
                                        <Gavel className="h-3 w-3" /> Recording & Sale Info
                                    </p>

                                    {/* Show existing data if available */}
                                    {(extLead.seq_num || extLead.last_sold_date || extLead.last_sold_price || extLead.docket || extLead.record_date) && (
                                        <div className="grid grid-cols-2 gap-3 text-sm mb-3">
                                            {extLead.seq_num && (
                                                <div className="p-3 bg-gray-800/50 rounded-lg">
                                                    <p className="text-xs text-gray-400">Sequence #</p>
                                                    <p className="font-medium text-white font-mono">{extLead.seq_num}</p>
                                                </div>
                                            )}
                                            {extLead.docket && (
                                                <div className="p-3 bg-gray-800/50 rounded-lg">
                                                    <p className="text-xs text-gray-400">Docket/Page</p>
                                                    <p className="font-medium text-white">{extLead.docket}{extLead.page ? ` / ${extLead.page}` : ''}</p>
                                                </div>
                                            )}
                                            {extLead.record_date && (
                                                <div className="p-3 bg-gray-800/50 rounded-lg">
                                                    <p className="text-xs text-gray-400">Recording Date</p>
                                                    <p className="font-medium text-white">
                                                        {typeof extLead.record_date === 'number'
                                                            ? new Date(extLead.record_date).toLocaleDateString()
                                                            : extLead.record_date}
                                                    </p>
                                                </div>
                                            )}
                                            {extLead.last_sold_date && (
                                                <div className="p-3 bg-gray-800/50 rounded-lg">
                                                    <p className="text-xs text-gray-400">Last Sale Date</p>
                                                    <p className="font-medium text-white">
                                                        {new Date(extLead.last_sold_date).toLocaleDateString()}
                                                    </p>
                                                </div>
                                            )}
                                            {extLead.last_sold_price && (
                                                <div className="p-3 bg-gray-800/50 rounded-lg">
                                                    <p className="text-xs text-gray-400">Last Sale Price</p>
                                                    <p className="font-medium text-green-400">{formatCurrency(extLead.last_sold_price)}</p>
                                                </div>
                                            )}
                                        </div>
                                    )}


                                </div>
                            </div>

                            {/* Location & Zoning Row */}
                            <div className="mt-3 pt-3 border-t border-gray-700">
                                <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">
                                    <MapPin className="h-3 w-3" /> Location & Zoning
                                </p>
                                <div className="grid grid-cols-2 gap-3 text-sm">
                                    <div className="p-3 bg-gray-800/50 rounded-lg">
                                        <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                                            <MapPin className="h-3 w-3" /> Zoning
                                        </div>
                                        <p className="font-medium text-white">{extLead.zoning || "Not Available"}</p>
                                        {extLead.municipality && (
                                            <p className="text-xs text-gray-500 mt-1">{extLead.municipality}</p>
                                        )}

                                    </div>
                                    <div className="p-3 bg-gray-800/50 rounded-lg">
                                        <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                                            <MapPin className="h-3 w-3" /> Neighborhood
                                        </div>
                                        <p className="font-medium text-white">{extLead.neighborhoods || "Unknown"}</p>
                                    </div>
                                    <div className="p-3 bg-gray-800/50 rounded-lg">
                                        <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                                            <MapPin className="h-3 w-3" /> Subdivision
                                        </div>
                                        <p className="font-medium text-white">{extLead.subdivision || "Unknown"}</p>
                                    </div>
                                    <div className="p-3 bg-gray-800/50 rounded-lg">
                                        <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                                            <Droplets className="h-3 w-3" /> Flood Zone
                                        </div>
                                        <p className={`font-medium ${extLead.flood_zone && !extLead.flood_zone.includes('X') ? 'text-yellow-400' : 'text-white'}`}>
                                            {getFloodZoneDescription(extLead.flood_zone)}
                                        </p>
                                    </div>
                                    <div className="p-3 bg-gray-800/50 rounded-lg">
                                        <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                                            <Building2 className="h-3 w-3" /> School District
                                        </div>
                                        <p className="font-medium text-white">{extLead.school_district || "Not Available"}</p>
                                    </div>
                                    <div className="p-3 bg-gray-800/50 rounded-lg">
                                        <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                                            <TrendingUp className="h-3 w-3" /> Path of Progress
                                        </div>
                                        <p className={`font-medium ${extLead.nearby_development ? 'text-green-400' : 'text-white'}`}>
                                            {extLead.nearby_development || "None Nearby"}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </AccordionContent>
                    </AccordionItem>

                    {/* Recorder Data - Moved here */}
                    <AccordionItem value="recorder" className="border-gray-700">
                        <AccordionTrigger className="text-white hover:text-green-400">
                            <div className="flex items-center gap-2">
                                <Gavel className="h-4 w-4 text-yellow-400" />
                                Recorder Data
                                {recordingHistory.length > 0 && (
                                    <Badge className="ml-2 bg-purple-500/20 text-purple-300 text-[10px]">
                                        {recordingHistory.length} found
                                    </Badge>
                                )}
                            </div>
                        </AccordionTrigger>
                        <AccordionContent>
                            {/* Recording History Lookup Button */}
                            {recordingHistory.length === 0 && !recordingError && (
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={handleLookupRecordings}
                                    disabled={isLoadingRecordings || !lead.owner_name}
                                    className="w-full bg-purple-900/20 border-purple-500/30 text-purple-400 hover:bg-purple-900/40 flex items-center justify-center gap-2"
                                >
                                    {isLoadingRecordings ? (
                                        <>
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                            Searching Recorder...
                                        </>
                                    ) : (
                                        <>
                                            <Search className="h-4 w-4" />
                                            Lookup Full Recording History
                                        </>
                                    )}
                                </Button>
                            )}

                            {recordingError && (
                                <p className="text-xs text-amber-400/70 mt-2 text-center">{recordingError}</p>
                            )}

                            {recordingHistory.length > 0 && (
                                <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                                    {recordingHistory.map((doc, i) => (
                                        <div
                                            key={doc.doc_id || i}
                                            className="flex items-center justify-between p-3 bg-gray-800/80 hover:bg-gray-700/80 rounded-lg border border-gray-700/50 transition-colors"
                                        >
                                            <div className="flex items-center gap-3 min-w-0 flex-1">
                                                <div className="w-2 h-2 rounded-full bg-purple-400 shrink-0" />
                                                <div className="min-w-0 flex-1">
                                                    <p className="text-sm font-medium text-white">
                                                        {doc.doc_type || 'DEED'}
                                                    </p>
                                                    <p className="text-xs text-gray-400 font-mono">
                                                        Doc #{doc.doc_number}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-3 shrink-0">
                                                <span className="text-xs text-gray-400">
                                                    {doc.record_date}
                                                </span>
                                                <a
                                                    href={`http://127.0.0.1:8000/api/v1/recorder/download/${doc.doc_id}`}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="p-1.5 rounded bg-purple-500/20 hover:bg-purple-500/40 text-purple-300 transition-colors"
                                                    title="Download PDF"
                                                    onClick={(e) => e.stopPropagation()}
                                                >
                                                    <Download className="h-3.5 w-3.5" />
                                                </a>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </AccordionContent>
                    </AccordionItem>

                    {/* Owner Information */}
                    <AccordionItem value="contact" className="border-gray-700">
                        <AccordionTrigger className="text-white hover:text-green-400">
                            <div className="flex items-center gap-2">
                                <User className="h-4 w-4 text-purple-400" />
                                Owner Information
                            </div>
                        </AccordionTrigger>
                        <AccordionContent>
                            <div className="space-y-3 text-sm">
                                <div className="p-3 bg-gray-800/50 rounded-lg">
                                    <p className="text-xs text-gray-400 mb-1">Owner Name</p>
                                    <p className="font-medium text-white">{lead.owner_name || "Unknown"}</p>
                                </div>
                                <div className="p-3 bg-gray-800/50 rounded-lg">
                                    <p className="text-xs text-gray-400 mb-1">Mailing Address</p>
                                    <p className="font-medium text-white">{lead.mailing_address || "Same as property"}</p>
                                </div>
                                <div className="grid grid-cols-2 gap-3">
                                    <div className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg">
                                        <Phone className="h-4 w-4 text-gray-400" />
                                        <div>
                                            <p className="text-xs text-gray-400">Phone</p>
                                            <p className="font-medium text-white">{extLead.phone || "Not Available"}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg">
                                        <Mail className="h-4 w-4 text-gray-400" />
                                        <div>
                                            <p className="text-xs text-gray-400">Email</p>
                                            <p className="font-medium text-white">{extLead.email || "Not Available"}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </AccordionContent>
                    </AccordionItem>

                    {/* Financials */}
                    <AccordionItem value="financials" className="border-gray-700">
                        <AccordionTrigger className="text-white hover:text-green-400">
                            <div className="flex items-center gap-2">
                                <DollarSign className="h-4 w-4 text-green-400" />
                                Financials & Equity
                            </div>
                        </AccordionTrigger>
                        <AccordionContent>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg">
                                    <span className="text-gray-400">Assessed Value</span>
                                    <span className="font-bold text-white">{formatCurrency(lead.assessed_value)}</span>
                                </div>
                                <div className="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg">
                                    <span className="text-gray-400">Estimated Value</span>
                                    <span className="font-bold text-green-400">{formatCurrency(extLead.estimated_value)}</span>
                                </div>
                                <div className="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg">
                                    <span className="text-gray-400">Price per Sqft</span>
                                    <span className="font-medium text-white">{extLead.price_per_sqft ? `$${extLead.price_per_sqft}/sqft` : "N/A"}</span>
                                </div>
                                <div className="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg">
                                    <span className="text-gray-400">HOA Fee</span>
                                    <span className="font-medium text-white">{extLead.hoa_fee !== undefined && extLead.hoa_fee !== null ? (extLead.hoa_fee === 0 ? "None" : `$${extLead.hoa_fee}/mo`) : "N/A"}</span>
                                </div>
                                <div className="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg">
                                    <span className="text-gray-400">Estimated ARV</span>
                                    <span className="font-bold text-green-400">{formatCurrency(lead.arv)}</span>
                                </div>
                                <div className="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg">
                                    <span className="text-gray-400">Last Sale Price</span>
                                    <span className="font-medium text-white">{formatCurrency(lead.last_sold_price)}</span>
                                </div>
                                <div className="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg">
                                    <span className="text-gray-400">Last Sale Date</span>
                                    <span className="font-medium text-white">{lead.last_sold_date || "N/A"}</span>
                                </div>
                            </div>
                        </AccordionContent>
                    </AccordionItem>

                    {/* Distress Signals */}
                    {(lead.distress_signals?.length || 0) > 0 && (
                        <AccordionItem value="distress" className="border-gray-700">
                            <AccordionTrigger className="text-white hover:text-green-400">
                                <div className="flex items-center gap-2">
                                    <AlertTriangle className="h-4 w-4 text-red-400" />
                                    Distress Signals
                                    <Badge className="ml-2 bg-red-500/20 text-red-400 text-[10px]">
                                        {lead.distress_signals?.length || 0} found
                                    </Badge>
                                </div>
                            </AccordionTrigger>
                            <AccordionContent>
                                <div className="space-y-2 text-sm">
                                    {/* Code Violations */}
                                    {extLead.violations && extLead.violations.length > 0 && (
                                        <div className="space-y-2">
                                            {extLead.violations.map((v, idx) => (
                                                <div key={idx} className="p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
                                                    <div className="font-medium text-red-400">{v.description}</div>
                                                    <div className="text-red-400/60 text-xs mt-1">Activity #: {v.activity_num}</div>
                                                </div>
                                            ))}
                                        </div>
                                    )}

                                    {/* Other Distress Signals */}
                                    {lead.distress_signals?.filter((s: string) => s !== "Code Violation").map((signal: string, idx: number) => (
                                        <div key={idx} className="p-3 bg-orange-900/20 border border-orange-500/30 rounded-lg text-orange-400">
                                            {signal}
                                        </div>
                                    ))}
                                </div>
                            </AccordionContent>
                        </AccordionItem>
                    )}



                </Accordion>

                {/* Action Buttons */}
                <div className="flex justify-between gap-3 mt-6 pt-4 border-t border-gray-700">
                    <div className="flex gap-2">
                        {onSwitchToListView && (
                            <Button
                                variant={currentViewMode === 'list' ? 'secondary' : 'outline'}
                                onClick={() => {
                                    onSwitchToListView()
                                    onOpenChange(false)
                                }}
                                className={currentViewMode === 'list'
                                    ? "bg-gray-700 text-white border-gray-600"
                                    : "border-gray-600 text-gray-300 hover:bg-gray-800"}
                            >
                                <ListIcon className="h-4 w-4 mr-2" />
                                List
                            </Button>
                        )}
                        {onSwitchToMapView && (
                            <Button
                                variant={currentViewMode === 'map' ? 'secondary' : 'outline'}
                                onClick={() => {
                                    onSwitchToMapView()
                                    onOpenChange(false)
                                }}
                                className={currentViewMode === 'map'
                                    ? "bg-gray-700 text-white border-gray-600"
                                    : "border-gray-600 text-gray-300 hover:bg-gray-800"}
                            >
                                <MapIcon className="h-4 w-4 mr-2" />
                                Map
                            </Button>
                        )}
                    </div>
                    <div className="flex gap-3">
                        <Button variant="outline" onClick={() => onOpenChange(false)} className="border-gray-600 text-gray-300 hover:bg-gray-800">
                            Close
                        </Button>
                        <Button className="bg-green-600 hover:bg-green-700 text-white">
                            Add to Campaign
                        </Button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    )
}
