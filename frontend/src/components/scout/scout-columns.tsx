"use client"

import { ColumnDef } from "@tanstack/react-table"
import { ArrowUpDown, MoreHorizontal, Eye, Download, AlertTriangle, Phone, Mail } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ScoutResult } from "@/lib/store"

// Helper to format currency
const formatCurrency = (value: number | undefined | null) => {
    if (!value && value !== 0) return "—"
    return `$${value?.toLocaleString()}`
}

// Helper to get flood zone badge color
const getFloodZoneBadgeClass = (zone: string | undefined) => {
    if (!zone) return "bg-gray-500/20 text-gray-400"
    const z = zone.toUpperCase()
    if (z.includes("X")) return "bg-green-500/20 text-green-400"
    if (z.includes("A") || z.includes("V")) return "bg-red-500/20 text-red-400"
    return "bg-yellow-500/20 text-yellow-400"
}

// Extended ScoutResult type with all GIS fields from LeadDetailDialog
type ExtendedScoutResult = ScoutResult & {
    // Property Details
    parcel_use_code?: string
    half_baths?: number
    stories?: number
    pool?: boolean
    garage?: boolean
    // Location & Zoning
    zoning?: string
    neighborhoods?: string
    municipality?: string
    flood_zone?: string
    school_district?: string
    nearby_development?: string
    development_status?: string
    // Owner Information
    phone?: string
    email?: string
    // Financials
    estimated_value?: number
    price_per_sqft?: number
    hoa_fee?: number
    equity?: number
    // MLS fields
    mls_source?: string
    mls_id?: string
    list_price?: number
    days_on_market?: number
    status?: string
}

interface ScoutColumnsOptions {
    onViewDetails?: (lead: ScoutResult) => void
    onImport?: (lead: ScoutResult) => void
}

export function createScoutColumns(options: ScoutColumnsOptions = {}): ColumnDef<ScoutResult>[] {
    return [
        // ============ CORE ============
        {
            accessorKey: "address",
            header: ({ column }) => (
                <Button
                    variant="ghost"
                    onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
                    className="text-left px-2"
                >
                    Address
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                </Button>
            ),
            cell: ({ row }) => {
                const lead = row.original as ExtendedScoutResult
                return (
                    <div className="flex flex-col min-w-[180px] px-2">
                        <span className="font-medium text-white truncate">{lead.address}</span>
                        <span className="text-xs text-gray-500">APN: {lead.parcel_id || "—"}</span>
                    </div>
                )
            },
        },

        // ============ PROPERTY DETAILS ============
        {
            accessorKey: "property_type",
            header: "Type",
            cell: ({ row }) => {
                const lead = row.original as ExtendedScoutResult
                const type = lead.property_type || "Unknown"
                return (
                    <div className="min-w-[120px]">
                        <Badge variant="outline" className="text-xs whitespace-nowrap">
                            {type}
                        </Badge>
                        {lead.parcel_use_code && (
                            <div className="text-[10px] text-gray-500 mt-0.5">Code: {lead.parcel_use_code}</div>
                        )}
                    </div>
                )
            },
        },
        {
            accessorKey: "year_built",
            header: ({ column }) => (
                <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")} className="px-2">
                    Year
                    <ArrowUpDown className="ml-1 h-3 w-3" />
                </Button>
            ),
            cell: ({ row }) => <div className="text-center px-2">{row.getValue("year_built") ?? "—"}</div>,
        },
        {
            accessorKey: "lot_size",
            header: "Lot Size",
            cell: ({ row }) => {
                const lot = row.getValue("lot_size") as number
                if (!lot) return <div className="text-right text-gray-500 px-2">—</div>
                if (lot >= 43560) {
                    return <div className="text-right px-2">{(lot / 43560).toFixed(2)} ac</div>
                }
                return <div className="text-right px-2">{lot.toLocaleString()} sf</div>
            },
        },
        {
            accessorKey: "sqft",
            header: ({ column }) => (
                <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")} className="px-2">
                    Living SqFt
                    <ArrowUpDown className="ml-1 h-3 w-3" />
                </Button>
            ),
            cell: ({ row }) => {
                const sqft = row.getValue("sqft") as number
                return <div className="text-right px-2">{sqft ? sqft.toLocaleString() : "—"}</div>
            },
        },
        {
            accessorKey: "beds",
            header: "Beds",
            cell: ({ row }) => <div className="text-center">{row.getValue("beds") ?? "—"}</div>,
        },
        {
            accessorKey: "baths",
            header: "Baths",
            cell: ({ row }) => {
                const lead = row.original as ExtendedScoutResult
                const baths = lead.baths ?? "—"
                const halfBaths = lead.half_baths ? `/${lead.half_baths}` : ""
                return <div className="text-center">{baths}{halfBaths}</div>
            },
        },
        {
            id: "stories",
            header: "Stories",
            cell: ({ row }) => {
                const lead = row.original as ExtendedScoutResult
                return <div className="text-center">{lead.stories ?? "—"}</div>
            },
        },

        // ============ LOCATION & ZONING ============
        {
            accessorKey: "zoning",
            header: "Zoning",
            cell: ({ row }) => {
                const lead = row.original as ExtendedScoutResult
                return (
                    <Badge variant="outline" className="text-xs">
                        {lead.zoning || "—"}
                    </Badge>
                )
            },
        },
        {
            id: "neighborhood",
            header: "Neighborhood",
            cell: ({ row }) => {
                const lead = row.original as ExtendedScoutResult
                return (
                    <div className="truncate max-w-[150px] text-sm" title={lead.neighborhoods}>
                        {lead.neighborhoods || "—"}
                    </div>
                )
            },
        },
        {
            accessorKey: "flood_zone",
            header: "Flood Zone",
            cell: ({ row }) => {
                const lead = row.original as ExtendedScoutResult
                if (!lead.flood_zone) return <span className="text-gray-500">—</span>
                return (
                    <Badge className={`text-xs ${getFloodZoneBadgeClass(lead.flood_zone)}`}>
                        {lead.flood_zone}
                    </Badge>
                )
            },
        },
        {
            id: "school_district",
            header: "School District",
            cell: ({ row }) => {
                const lead = row.original as ExtendedScoutResult
                return (
                    <div className="truncate max-w-[150px] text-xs" title={lead.school_district}>
                        {lead.school_district || "—"}
                    </div>
                )
            },
        },
        {
            id: "path_of_progress",
            header: "Path of Progress",
            cell: ({ row }) => {
                const lead = row.original as ExtendedScoutResult
                const hasProgress = lead.nearby_development && lead.nearby_development !== "None Nearby"
                return (
                    <span className={hasProgress ? "text-green-400" : "text-gray-500"}>
                        {lead.nearby_development || "None"}
                    </span>
                )
            },
        },

        // ============ OWNER INFORMATION ============
        {
            accessorKey: "owner_name",
            header: ({ column }) => (
                <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")} className="px-2">
                    Owner
                    <ArrowUpDown className="ml-1 h-3 w-3" />
                </Button>
            ),
            cell: ({ row }) => {
                const owner = row.getValue("owner_name") as string
                return <div className="truncate max-w-[140px] px-2">{owner || "Unknown"}</div>
            },
        },
        {
            accessorKey: "mailing_address",
            header: "Mailing Address",
            cell: ({ row }) => {
                const addr = row.getValue("mailing_address") as string
                return (
                    <div className="truncate max-w-[150px] text-xs" title={addr}>
                        {addr || "Same as property"}
                    </div>
                )
            },
        },
        {
            id: "contact",
            header: "Contact",
            cell: ({ row }) => {
                const lead = row.original as ExtendedScoutResult
                const hasPhone = lead.phone
                const hasEmail = lead.email
                if (!hasPhone && !hasEmail) return <span className="text-gray-500">—</span>
                return (
                    <div className="flex items-center gap-1">
                        {hasPhone && <Phone className="h-3 w-3 text-green-400" />}
                        {hasEmail && <Mail className="h-3 w-3 text-blue-400" />}
                    </div>
                )
            },
        },

        // ============ FINANCIALS & EQUITY ============
        {
            accessorKey: "assessed_value",
            header: ({ column }) => (
                <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")} className="px-2">
                    Assessed
                    <ArrowUpDown className="ml-1 h-3 w-3" />
                </Button>
            ),
            cell: ({ row }) => {
                const value = row.getValue("assessed_value") as number
                return <div className="text-right font-medium px-2">{formatCurrency(value)}</div>
            },
        },
        {
            id: "estimated_value",
            header: ({ column }) => (
                <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")} className="px-2">
                    Est. Value
                    <ArrowUpDown className="ml-1 h-3 w-3" />
                </Button>
            ),
            cell: ({ row }) => {
                const lead = row.original as ExtendedScoutResult
                return (
                    <div className="text-right font-medium text-green-400 px-2">
                        {formatCurrency(lead.estimated_value)}
                    </div>
                )
            },
        },
        {
            id: "price_per_sqft",
            header: "$/SqFt",
            cell: ({ row }) => {
                const lead = row.original as ExtendedScoutResult
                return (
                    <div className="text-right text-sm">
                        {lead.price_per_sqft ? `$${lead.price_per_sqft}` : "—"}
                    </div>
                )
            },
        },
        {
            id: "hoa_fee",
            header: "HOA",
            cell: ({ row }) => {
                const lead = row.original as ExtendedScoutResult
                if (lead.hoa_fee === undefined || lead.hoa_fee === null) return <span className="text-gray-500">—</span>
                if (lead.hoa_fee === 0) return <span className="text-green-400">None</span>
                return <span>${lead.hoa_fee}/mo</span>
            },
        },
        {
            accessorKey: "arv",
            header: ({ column }) => (
                <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")} className="px-2">
                    ARV
                    <ArrowUpDown className="ml-1 h-3 w-3" />
                </Button>
            ),
            cell: ({ row }) => {
                const arv = row.getValue("arv") as number
                return <div className="text-right font-bold text-green-400 px-2">{formatCurrency(arv)}</div>
            },
        },
        {
            id: "last_sold",
            header: "Last Sold",
            cell: ({ row }) => {
                const lead = row.original
                const date = lead.last_sold_date
                const price = lead.last_sold_price
                if (!date && !price) return <span className="text-gray-500">—</span>
                return (
                    <div className="text-xs">
                        {price && <div>{formatCurrency(price)}</div>}
                        {date && <div className="text-gray-400">{new Date(date).toLocaleDateString()}</div>}
                    </div>
                )
            },
        },

        // ============ DISTRESS SIGNALS ============
        {
            accessorKey: "distress_signals",
            header: "Distress",
            cell: ({ row }) => {
                const signals = row.getValue("distress_signals") as string[]
                if (!signals || signals.length === 0) {
                    return <span className="text-gray-500">—</span>
                }
                return (
                    <div className="flex items-center gap-1">
                        <AlertTriangle className="h-3 w-3 text-red-400" />
                        <Badge className="bg-red-500/20 text-red-400 text-xs">
                            {signals.length}
                        </Badge>
                    </div>
                )
            },
        },

        // ============ ACTIONS ============
        {
            id: "actions",
            cell: ({ row }) => {
                const lead = row.original

                return (
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0">
                                <span className="sr-only">Open menu</span>
                                <MoreHorizontal className="h-4 w-4" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="bg-gray-900 border-gray-700">
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuItem
                                onClick={() => options.onViewDetails?.(lead)}
                                className="cursor-pointer"
                            >
                                <Eye className="mr-2 h-4 w-4" />
                                View Details
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                                onClick={() => options.onImport?.(lead)}
                                className="cursor-pointer"
                            >
                                <Download className="mr-2 h-4 w-4" />
                                Import to Inbox
                            </DropdownMenuItem>
                            <DropdownMenuItem
                                onClick={() => navigator.clipboard.writeText(lead.id)}
                                className="cursor-pointer"
                            >
                                Copy Lead ID
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                )
            },
        },
    ]
}
