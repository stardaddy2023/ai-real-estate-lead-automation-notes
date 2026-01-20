"use client"

import { ColumnDef } from "@tanstack/react-table"
import { ArrowUpDown, MoreHorizontal, Phone, Mail, Loader2, Zap } from "lucide-react"
import Link from "next/link"

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
import { Lead } from "@/types"

// Column options type for callbacks
export interface InboxColumnOptions {
    onEnrich?: (lead: Lead) => void
    enrichingIds?: Set<string>
    selectedIds?: Set<string>
    onToggleSelect?: (id: string) => void
    onToggleAll?: () => void
    allSelected?: boolean
}

export function createInboxColumns(options: InboxColumnOptions = {}): ColumnDef<Lead>[] {
    return [
        // Checkbox Column
        {
            id: "select",
            header: () => (
                <div className="flex items-center justify-center px-1">
                    <input
                        type="checkbox"
                        checked={options.allSelected || false}
                        onChange={() => options.onToggleAll?.()}
                        className="w-4 h-4 rounded border-gray-400 dark:border-gray-600 text-green-600 focus:ring-green-500 bg-white dark:bg-gray-700 cursor-pointer"
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>
            ),
            cell: ({ row }) => {
                const lead = row.original
                const isSelected = options.selectedIds?.has(lead.id) || false
                return (
                    <div className="flex items-center justify-center px-1">
                        <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => options.onToggleSelect?.(lead.id)}
                            className="w-4 h-4 rounded border-gray-400 dark:border-gray-600 text-green-600 focus:ring-green-500 bg-white dark:bg-gray-700 cursor-pointer"
                            onClick={(e) => e.stopPropagation()}
                        />
                    </div>
                )
            },
            size: 40,
        },
        // Address Column
        {
            accessorKey: "address_street",
            header: ({ column }) => {
                return (
                    <Button
                        variant="ghost"
                        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
                    >
                        Address
                        <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                )
            },
            cell: ({ row }) => {
                const lead = row.original
                return (
                    <div className="flex flex-col min-w-[180px]">
                        <Link href={`/leads/${lead.id}`} className="font-medium hover:underline text-gray-900 dark:text-white">
                            {lead.address_street}
                        </Link>
                        <span className="text-xs text-muted-foreground">{lead.address_zip}</span>
                    </div>
                )
            },
        },
        // Status Column with Badge
        {
            accessorKey: "status",
            header: "Status",
            cell: ({ row }) => {
                const status = row.getValue("status") as string
                let variant: "default" | "secondary" | "destructive" | "outline" = "outline"
                let colorClass = ""

                if (status === "New") {
                    colorClass = "bg-blue-500/20 text-blue-400 border-blue-500/50"
                } else if (status === "Skiptraced") {
                    colorClass = "bg-green-500/20 text-green-400 border-green-500/50"
                } else if (status === "Contacted") {
                    colorClass = "bg-yellow-500/20 text-yellow-400 border-yellow-500/50"
                } else if (status === "Offer") {
                    colorClass = "bg-purple-500/20 text-purple-400 border-purple-500/50"
                }

                return (
                    <Badge variant={variant} className={`text-xs ${colorClass}`}>
                        {status}
                    </Badge>
                )
            },
        },
        // Owner Column
        {
            accessorKey: "owner_name",
            header: ({ column }) => (
                <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
                    Owner
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                </Button>
            ),
            cell: ({ row }) => {
                return <div className="truncate max-w-[140px] text-gray-900 dark:text-white">{row.getValue("owner_name") || "Unknown"}</div>
            },
        },
        // Contact Column (Phone + Email icons)
        {
            id: "contact",
            header: "Contact",
            cell: ({ row }) => {
                const lead = row.original
                const hasPhone = lead.phone
                const hasEmail = lead.email

                if (!hasPhone && !hasEmail) {
                    return <span className="text-gray-500 text-sm">—</span>
                }

                return (
                    <div className="flex items-center gap-2">
                        {hasPhone && (
                            <div className="flex items-center gap-1" title={lead.phone || ""}>
                                <Phone className="h-3 w-3 text-green-400" />
                                <span className="text-xs text-gray-300 hidden lg:inline">{lead.phone}</span>
                            </div>
                        )}
                        {hasEmail && (
                            <div className="flex items-center gap-1" title={lead.email || ""}>
                                <Mail className="h-3 w-3 text-blue-400" />
                            </div>
                        )}
                    </div>
                )
            },
        },
        // Property Type Column
        {
            accessorKey: "property_type",
            header: "Type",
            cell: ({ row }) => {
                const type = row.getValue("property_type") as string
                return (
                    <Badge variant="outline" className="text-xs whitespace-nowrap">
                        {type || "Unknown"}
                    </Badge>
                )
            },
        },
        // Score Column
        {
            accessorKey: "distress_score",
            header: ({ column }) => {
                return (
                    <Button
                        variant="ghost"
                        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
                    >
                        Score
                        <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                )
            },
            cell: ({ row }) => {
                const score = parseFloat(row.getValue("distress_score") || "0")
                let colorClass = "text-yellow-600"
                if (score > 80) colorClass = "text-green-600"
                else if (score < 50) colorClass = "text-red-600"

                return <div className={`font-bold ${colorClass}`}>{score || "—"}</div>
            },
        },
        // Actions Column
        {
            id: "actions",
            cell: ({ row }) => {
                const lead = row.original
                const isEnriching = options.enrichingIds?.has(lead.id)

                return (
                    <div className="flex items-center gap-2">
                        {/* Quick Enrich Button */}
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => options.onEnrich?.(lead)}
                            disabled={isEnriching || lead.status === "Skiptraced"}
                            className="h-8 px-2"
                            title={lead.status === "Skiptraced" ? "Already enriched" : "Skip Trace"}
                        >
                            {isEnriching ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                <Zap className={`h-4 w-4 ${lead.status === "Skiptraced" ? "text-gray-500" : "text-yellow-400"}`} />
                            )}
                        </Button>

                        {/* Dropdown Menu */}
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" className="h-8 w-8 p-0">
                                    <span className="sr-only">Open menu</span>
                                    <MoreHorizontal className="h-4 w-4" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="bg-gray-900 border-gray-700">
                                <DropdownMenuLabel>Actions</DropdownMenuLabel>
                                <DropdownMenuItem asChild>
                                    <Link href={`/leads/${lead.id}`}>View Details</Link>
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                    onClick={() => options.onEnrich?.(lead)}
                                    disabled={isEnriching}
                                >
                                    <Zap className="mr-2 h-4 w-4" />
                                    Skip Trace
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                    onClick={() => navigator.clipboard.writeText(lead.id)}
                                >
                                    Copy Lead ID
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                )
            },
        },
    ]
}

// Default static columns for backward compatibility
export const columns = createInboxColumns()
