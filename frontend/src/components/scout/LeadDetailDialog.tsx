import React from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { ScoutResult } from './LeadScout'
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Building2, MapPin, User, Phone, Mail, DollarSign, Calendar, Ruler } from 'lucide-react'

interface LeadDetailDialogProps {
    lead: ScoutResult | null
    open: boolean
    onOpenChange: (open: boolean) => void
}

import { SimpleAccordion, SimpleAccordionItem, SimpleAccordionTrigger, SimpleAccordionContent } from "@/components/ui/simple-accordion"
import { AlertTriangle, FileText, Gavel } from 'lucide-react'

export function LeadDetailDialog({ lead, open, onOpenChange }: LeadDetailDialogProps) {
    if (!lead) return null

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="text-2xl font-bold flex items-center gap-2 flex-wrap">
                        {lead.address}
                        {lead.distress_signals?.map((signal, i) => (
                            <Badge key={i} variant="destructive">
                                {signal}
                            </Badge>
                        ))}
                    </DialogTitle>

                </DialogHeader>
                <div className="px-6 pb-2 -mt-2 text-sm text-gray-400">
                    APN: {lead.parcel_id || "Unknown"}
                </div>

                <SimpleAccordion className="w-full mt-4">
                    {/* Contact Info */}
                    <SimpleAccordionItem value="contact">
                        <SimpleAccordionTrigger>
                            <div className="flex items-center gap-2"><User className="h-5 w-5" /> Contact Information</div>
                        </SimpleAccordionTrigger>
                        <SimpleAccordionContent>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="flex items-center gap-3 p-3 border rounded-md bg-muted/20">
                                    <Phone className="h-5 w-5 text-muted-foreground" />
                                    <div>
                                        <p className="text-xs text-muted-foreground">Phone</p>
                                        <p className="font-medium">{lead.phone || "Not Available"}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3 p-3 border rounded-md bg-muted/20">
                                    <Mail className="h-5 w-5 text-muted-foreground" />
                                    <div>
                                        <p className="text-xs text-muted-foreground">Email</p>
                                        <p className="font-medium">{lead.email || "Not Available"}</p>
                                    </div>
                                </div>
                                <div className="col-span-2 pt-2">
                                    <span className="text-muted-foreground block mb-1">Owner Name:</span>
                                    <p className="font-medium">{lead.owner_name}</p>
                                </div>
                                <div className="col-span-2 pt-2">
                                    <span className="text-muted-foreground block mb-1">Mailing Address:</span>
                                    <p className="font-medium">{lead.mailing_address}</p>
                                </div>
                            </div>
                        </SimpleAccordionContent>
                    </SimpleAccordionItem>

                    {/* Property Details */}
                    <SimpleAccordionItem value="property">
                        <SimpleAccordionTrigger>
                            <div className="flex items-center gap-2"><Building2 className="h-5 w-5" /> Property Details</div>
                        </SimpleAccordionTrigger>
                        <SimpleAccordionContent>
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div><span className="text-muted-foreground">Type:</span> <p className="font-medium">{lead.property_type}</p></div>
                                <div><span className="text-muted-foreground">Year Built:</span> <p className="font-medium">{lead.year_built || "N/A"}</p></div>
                                <div><span className="text-muted-foreground">Sqft:</span> <p className="font-medium">{lead.sqft ? `${lead.sqft.toLocaleString()} sqft` : "N/A"}</p></div>
                                <div><span className="text-muted-foreground">Lot Size:</span> <p className="font-medium">{lead.lot_size ? `${lead.lot_size.toLocaleString()} sqft` : "N/A"}</p></div>
                                <div><span className="text-muted-foreground">Beds:</span> <p className="font-medium">{lead.beds || "N/A"}</p></div>
                                <div><span className="text-muted-foreground">Baths:</span> <p className="font-medium">{lead.baths || "N/A"}</p></div>
                                <div><span className="text-muted-foreground">Pool:</span> <p className="font-medium">{lead.pool ? "Yes" : "No/Unknown"}</p></div>
                                <div><span className="text-muted-foreground">Garage:</span> <p className="font-medium">{lead.garage ? "Yes" : "No/Unknown"}</p></div>
                            </div>
                        </SimpleAccordionContent>
                    </SimpleAccordionItem>

                    {/* Financials */}
                    <SimpleAccordionItem value="financials">
                        <SimpleAccordionTrigger>
                            <div className="flex items-center gap-2"><DollarSign className="h-5 w-5" /> Financials & Equity</div>
                        </SimpleAccordionTrigger>
                        <SimpleAccordionContent>
                            <div className="space-y-3 text-sm">
                                <div className="flex justify-between border-b pb-2">
                                    <span className="text-muted-foreground">Estimated ARV:</span>
                                    <span className="font-bold text-green-600">{lead.arv ? `$${lead.arv.toLocaleString()}` : "N/A"}</span>
                                </div>
                                <div className="flex justify-between border-b pb-2">
                                    <span className="text-muted-foreground">Last Sale Price:</span>
                                    <span>{lead.last_sale_price ? `$${lead.last_sale_price.toLocaleString()}` : "N/A"}</span>
                                </div>
                                <div className="flex justify-between border-b pb-2">
                                    <span className="text-muted-foreground">Last Sale Date:</span>
                                    <span>{lead.last_sale_date || "N/A"}</span>
                                </div>
                            </div>
                        </SimpleAccordionContent>
                    </SimpleAccordionItem>

                    {/* Distressed Info */}
                    <SimpleAccordionItem value="distress">
                        <SimpleAccordionTrigger>
                            <div className="flex items-center gap-2"><AlertTriangle className="h-5 w-5" /> Distressed Info</div>
                        </SimpleAccordionTrigger>
                        <SimpleAccordionContent>
                            <div className="space-y-3 text-sm">
                                {/* Show individual violations if present */}
                                {lead.violations && lead.violations.length > 0 && (
                                    <div className="space-y-2">
                                        <div className="font-semibold text-red-600 flex items-center gap-2">
                                            <AlertTriangle className="h-4 w-4" />
                                            Code Violations ({lead.violations.length})
                                        </div>
                                        {lead.violations.map((v: { description: string; activity_num: string }, idx: number) => (
                                            <div key={idx} className="p-2 bg-red-50 border border-red-100 rounded text-red-700 text-xs">
                                                <div className="font-medium">{v.description}</div>
                                                <div className="text-red-500 text-[10px]">Activity #: {v.activity_num}</div>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* Show other distress signals (non-violation) */}
                                {lead.distress_signals?.filter((s: string) => s !== "Code Violation").map((signal: string, idx: number) => (
                                    <div key={idx} className="p-2 bg-red-50 border border-red-100 rounded text-red-700">
                                        {signal}
                                    </div>
                                ))}

                                {/* Show message if no distress signals at all */}
                                {(!lead.distress_signals || lead.distress_signals.length === 0) && (!lead.violations || lead.violations.length === 0) && (
                                    <p className="text-muted-foreground">No distress signals detected.</p>
                                )}
                            </div>
                        </SimpleAccordionContent>
                    </SimpleAccordionItem>



                    {/* Recorder Data (MCP Placeholder) */}
                    <SimpleAccordionItem value="recorder">
                        <SimpleAccordionTrigger>
                            <div className="flex items-center gap-2"><Gavel className="h-5 w-5" /> Recorder Data (Liens/Judgments)</div>
                        </SimpleAccordionTrigger>
                        <SimpleAccordionContent>
                            <div className="p-4 border border-dashed rounded-md text-center text-muted-foreground bg-muted/10">
                                <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
                                <p>Recorder data integration coming soon.</p>
                                <p className="text-xs">Will fetch Liens, Judgments, and Foreclosure notices.</p>
                            </div>
                        </SimpleAccordionContent>
                    </SimpleAccordionItem>

                </SimpleAccordion>

                <div className="flex justify-end gap-2 mt-6">
                    <Button variant="outline" onClick={() => onOpenChange(false)}>Close</Button>
                    <Button>Add to Campaign</Button>
                </div>
            </DialogContent>
        </Dialog>
    )
}
