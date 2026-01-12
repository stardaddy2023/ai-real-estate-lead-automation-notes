import React from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { ScoutResult } from '@/lib/store'
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { User, Phone, Mail, Building2, DollarSign, AlertTriangle, Gavel, FileText, MapPin, Droplets, TrendingUp, Home, Calendar, Ruler } from 'lucide-react'
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/simple-accordion"

interface LeadDetailDialogProps {
    lead: ScoutResult | null
    open: boolean
    onOpenChange: (open: boolean) => void
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

export function LeadDetailDialog({ lead, open, onOpenChange }: LeadDetailDialogProps) {
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
        pool?: boolean
        garage?: boolean
        // HomeHarvest/MLS fields
        half_baths?: number
        stories?: number
        neighborhoods?: string
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
    }

    // Check if this is an MLS listing (has listing-specific data)
    const isMLSListing = extLead.source === "homeharvest_mls" || extLead.mls_source || extLead.list_price

    // Check if location section has data
    const hasLocationData = extLead.zoning || extLead.flood_zone || extLead.school_district || extLead.nearby_development

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto bg-gradient-to-br from-gray-900 to-gray-950 border-gray-700">
                {/* Header */}
                <DialogHeader className="pb-4 border-b border-gray-700">
                    <div className="flex items-start justify-between gap-4">
                        {/* Property Photo Thumbnail */}
                        {extLead.primary_photo && (
                            <div className="flex-shrink-0">
                                <img
                                    src={extLead.primary_photo}
                                    alt={lead.address}
                                    className="w-24 h-24 object-cover rounded-lg border border-gray-600"
                                />
                            </div>
                        )}
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
                        </div>
                    </div>
                </DialogHeader>

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

                <Accordion type="single" collapsible defaultValue={isMLSListing ? "listing" : "property"} className="w-full mt-2">

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

                                {/* Assessor Link - only show for non-MLS leads (MLS has "View Original Listing" in Listing Details) */}
                                {extLead.assessor_url && !isMLSListing && (
                                    <div className="mt-3 pt-3 border-t border-gray-700">
                                        <a href={extLead.assessor_url} target="_blank" rel="noopener noreferrer" className="flex items-center justify-center w-full p-2 bg-blue-900/20 border border-blue-500/30 rounded-lg text-blue-400 hover:bg-blue-900/40 transition-colors text-sm gap-2">
                                            <FileText className="h-4 w-4" />
                                            View Official Assessor Record
                                        </a>
                                    </div>
                                )}
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

                    {/* Recorder Data */}
                    <AccordionItem value="recorder" className="border-gray-700">
                        <AccordionTrigger className="text-white hover:text-green-400">
                            <div className="flex items-center gap-2">
                                <Gavel className="h-4 w-4 text-yellow-400" />
                                Recorder Data
                            </div>
                        </AccordionTrigger>
                        <AccordionContent>
                            <div className="p-6 border border-dashed border-gray-600 rounded-lg text-center bg-gray-800/30">
                                <FileText className="h-8 w-8 mx-auto mb-2 text-gray-500" />
                                <p className="text-gray-400">Recorder data integration coming soon.</p>
                                <p className="text-xs text-gray-500 mt-1">Liens, Judgments, and Foreclosure notices</p>
                            </div>
                        </AccordionContent>
                    </AccordionItem>

                </Accordion>

                {/* Action Buttons */}
                <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-700">
                    <Button variant="outline" onClick={() => onOpenChange(false)} className="border-gray-600 text-gray-300 hover:bg-gray-800">
                        Close
                    </Button>
                    <Button className="bg-green-600 hover:bg-green-700 text-white">
                        Add to Campaign
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    )
}
