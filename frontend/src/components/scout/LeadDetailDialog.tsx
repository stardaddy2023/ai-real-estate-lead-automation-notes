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
    if (!value) return "N/A"
    return `$${value.toLocaleString()}`
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
    }

    // Check if location section has data
    const hasLocationData = extLead.zoning || extLead.flood_zone || extLead.school_district || extLead.nearby_development

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto bg-gradient-to-br from-gray-900 to-gray-950 border-gray-700">
                {/* Header */}
                <DialogHeader className="pb-4 border-b border-gray-700">
                    <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                            <DialogTitle className="text-xl font-bold text-white flex items-center gap-3 flex-wrap">
                                <Home className="h-5 w-5 text-green-400" />
                                {lead.address}
                            </DialogTitle>
                            <p className="text-sm text-gray-400 mt-1">APN: {lead.parcel_id || "Unknown"}</p>
                        </div>
                        <div className="flex flex-wrap gap-1 max-w-[200px]">
                            {lead.distress_signals?.slice(0, 3).map((signal, i) => (
                                <Badge key={i} className="bg-red-500/20 text-red-400 border-red-500/50 text-xs">
                                    {signal}
                                </Badge>
                            ))}
                        </div>
                    </div>
                </DialogHeader>

                {/* Quick Stats Bar */}
                <div className="grid grid-cols-4 gap-2 py-4 border-b border-gray-700">
                    <div className="text-center">
                        <div className="text-2xl font-bold text-white">{lead.beds || "—"}</div>
                        <div className="text-xs text-gray-400">Beds</div>
                    </div>
                    <div className="text-center">
                        <div className="text-2xl font-bold text-white">{lead.baths || "—"}</div>
                        <div className="text-xs text-gray-400">Baths</div>
                    </div>
                    <div className="text-center">
                        <div className="text-2xl font-bold text-white">{lead.sqft ? lead.sqft.toLocaleString() : "—"}</div>
                        <div className="text-xs text-gray-400">Sqft</div>
                    </div>
                    <div className="text-center">
                        <div className="text-2xl font-bold text-green-400">{formatCurrency(lead.assessed_value)}</div>
                        <div className="text-xs text-gray-400">Assessed</div>
                    </div>
                </div>

                <Accordion type="single" collapsible defaultValue="property" className="w-full mt-2">

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
                                            <Droplets className="h-3 w-3" /> Flood Zone
                                        </div>
                                        <p className={`font-medium ${extLead.flood_zone ? 'text-yellow-400' : 'text-white'}`}>
                                            {extLead.flood_zone || "None Detected"}
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
