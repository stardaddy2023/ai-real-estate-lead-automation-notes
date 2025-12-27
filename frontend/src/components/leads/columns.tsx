"use client"

import { ColumnDef } from "@tanstack/react-table"
import { ArrowUpDown, MoreHorizontal } from "lucide-react"
import Link from "next/link"

import { Button } from "@/components/ui/button"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Lead } from "@/types"

export const columns: ColumnDef<Lead>[] = [
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
                <div className="flex flex-col">
                    <Link href={`/leads/${lead.id}`} className="font-medium hover:underline">
                        {lead.address_street}
                    </Link>
                    <span className="text-xs text-muted-foreground">{lead.address_zip}</span>
                </div>
            )
        },
    },
    {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => {
            const status = row.getValue("status") as string
            let colorClass = "bg-slate-100 text-slate-800"

            if (status === "new") colorClass = "bg-blue-100 text-blue-800"
            else if (status === "contacted") colorClass = "bg-yellow-100 text-yellow-800"
            else if (status === "offer_made") colorClass = "bg-green-100 text-green-800"

            return (
                <div className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${colorClass}`}>
                    {status}
                </div>
            )
        },
    },
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
            const score = parseFloat(row.getValue("distress_score"))
            let colorClass = "text-yellow-600"
            if (score > 80) colorClass = "text-green-600"
            else if (score < 50) colorClass = "text-red-600"

            return <div className={`font-bold ${colorClass}`}>{score}</div>
        },
    },
    {
        accessorKey: "owner_name",
        header: "Owner",
        cell: ({ row }) => {
            return <div>{row.getValue("owner_name") || "Unknown"}</div>
        },
    },
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
                    <DropdownMenuContent align="end">
                        <DropdownMenuLabel>Actions</DropdownMenuLabel>
                        <DropdownMenuItem
                            onClick={() => navigator.clipboard.writeText(lead.id)}
                        >
                            Copy Lead ID
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem asChild>
                            <Link href={`/leads/${lead.id}`}>View Details</Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => console.log("Enriching lead:", lead.id)}>
                            Enrich Data
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            )
        },
    },
]
