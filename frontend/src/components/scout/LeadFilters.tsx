"use client"

import React, { useState } from 'react'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Button } from '@/components/ui/button'
import { Filter, X, RotateCcw } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Separator } from '@/components/ui/separator'

export const PROPERTY_TYPES = [
    "Single Family",
    "Multi Family",
    "Condo",
    "Vacant Land",
    "Commercial",
    "Mobile Home Park",
    "Industrial / Storage",
    "Parking",
    "Partially Complete",
    "Salvage / Teardown",
    "Mixed Use"
]
export const DISTRESS_TYPES = [
    "Code Violations",
    "Absentee Owner",
    "Liens (HOA, Mechanics)",
    "Pre-Foreclosure",
    "Divorce",
    "Judgements",
    "Tax Liens",
    "Unpaid Taxes",
    "Probate",
    "Eviction"
]
export const DISABLED_DISTRESS_TYPES = ["Unpaid Taxes", "Probate", "Eviction"]

interface LeadFiltersProps {
    selectedPropertyTypes: string[]
    setSelectedPropertyTypes: (types: string[]) => void
    selectedDistressTypes: string[]
    setSelectedDistressTypes: (types: string[]) => void
    minBeds: string
    setMinBeds: (val: string) => void
    minBaths: string
    setMinBaths: (val: string) => void
    minSqft: string
    setMinSqft: (val: string) => void
    onSearch: () => void
}

export function LeadFilters({
    selectedPropertyTypes,
    setSelectedPropertyTypes,
    selectedDistressTypes,
    setSelectedDistressTypes,
    minBeds,
    setMinBeds,
    minBaths,
    setMinBaths,
    minSqft,
    setMinSqft,
    onSearch
}: LeadFiltersProps) {
    const [open, setOpen] = useState(false)

    const handleReset = () => {
        setSelectedPropertyTypes([])
        setSelectedDistressTypes([])
        setMinBeds("")
        setMinBaths("")
        setMinSqft("")
    }

    const handleApply = () => {
        setOpen(false)
        onSearch()
    }

    const togglePropertyType = (type: string) => {
        if (selectedPropertyTypes.includes(type)) {
            setSelectedPropertyTypes(selectedPropertyTypes.filter(t => t !== type))
        } else {
            setSelectedPropertyTypes([...selectedPropertyTypes, type])
        }
    }

    const toggleDistressType = (type: string) => {
        if (selectedDistressTypes.includes(type)) {
            setSelectedDistressTypes(selectedDistressTypes.filter(t => t !== type))
        } else {
            setSelectedDistressTypes([...selectedDistressTypes, type])
        }
    }

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button variant="outline" className="h-10 bg-white dark:bg-gray-950 border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 gap-2 shadow-lg">
                    <Filter className="w-4 h-4" />
                    <span className="hidden sm:inline">Filters</span>
                    {(selectedPropertyTypes.length + selectedDistressTypes.length) > 0 && (
                        <span className="bg-blue-600 text-white text-[10px] px-1.5 py-0.5 rounded-full">
                            {selectedPropertyTypes.length + selectedDistressTypes.length}
                        </span>
                    )}
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[340px] p-0 bg-white dark:bg-gray-950 border-gray-200 dark:border-gray-800 shadow-xl" align="end">
                <div className="flex items-center justify-between p-4 border-b border-gray-100 dark:border-gray-800">
                    <h3 className="font-semibold text-lg">Lead Filters</h3>
                    <div className="flex items-center gap-2">
                        <Button variant="ghost" size="sm" className="h-8 px-2 text-xs text-muted-foreground hover:text-foreground" onClick={handleReset}>
                            <RotateCcw className="w-3 h-3 mr-1" /> Reset
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setOpen(false)}>
                            <X className="w-4 h-4" />
                        </Button>
                    </div>
                </div>

                <ScrollArea className="h-[500px] p-4">
                    <div className="space-y-6">

                        {/* Property Types */}
                        <div className="space-y-3">
                            <h4 className="font-medium text-sm text-gray-900 dark:text-gray-100">Property Type</h4>
                            <div className="grid grid-cols-1 gap-2">
                                {PROPERTY_TYPES.map(type => (
                                    <div key={type} className="flex items-center space-x-2">
                                        <Checkbox
                                            id={`type-${type}`}
                                            checked={selectedPropertyTypes.includes(type)}
                                            onCheckedChange={() => togglePropertyType(type)}
                                        />
                                        <label
                                            htmlFor={`type-${type}`}
                                            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                                        >
                                            {type}
                                        </label>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <Separator />

                        {/* Distress Signals */}
                        <div className="space-y-3">
                            <h4 className="font-medium text-sm text-gray-900 dark:text-gray-100">Distress Signals</h4>
                            <div className="grid grid-cols-1 gap-2">
                                {DISTRESS_TYPES.map(type => (
                                    <div key={type} className="flex items-center space-x-2">
                                        <Checkbox
                                            id={`distress-${type}`}
                                            checked={selectedDistressTypes.includes(type)}
                                            onCheckedChange={() => toggleDistressType(type)}
                                            disabled={DISABLED_DISTRESS_TYPES.includes(type)}
                                        />
                                        <label
                                            htmlFor={`distress-${type}`}
                                            className={`text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer ${DISABLED_DISTRESS_TYPES.includes(type) ? 'text-gray-400' : ''}`}
                                        >
                                            {type}
                                        </label>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <Separator />

                        {/* Advanced Filters */}
                        <div className="space-y-3">
                            <h4 className="font-medium text-sm text-gray-900 dark:text-gray-100">Property Details</h4>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1">
                                    <Label className="text-xs text-muted-foreground">Min Beds</Label>
                                    <input
                                        type="number"
                                        className="w-full bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                                        value={minBeds}
                                        onChange={(e) => setMinBeds(e.target.value)}
                                        placeholder="Any"
                                    />
                                </div>
                                <div className="space-y-1">
                                    <Label className="text-xs text-muted-foreground">Min Baths</Label>
                                    <input
                                        type="number"
                                        className="w-full bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                                        value={minBaths}
                                        onChange={(e) => setMinBaths(e.target.value)}
                                        placeholder="Any"
                                    />
                                </div>
                                <div className="space-y-1 col-span-2">
                                    <Label className="text-xs text-muted-foreground">Min Sqft</Label>
                                    <input
                                        type="number"
                                        className="w-full bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                                        value={minSqft}
                                        onChange={(e) => setMinSqft(e.target.value)}
                                        placeholder="Any"
                                    />
                                </div>
                            </div>
                        </div>

                    </div>
                </ScrollArea>

                <div className="p-4 border-t border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/50">
                    <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white" onClick={handleApply}>
                        View Results
                    </Button>
                </div>
            </PopoverContent>
        </Popover>
    )
}
