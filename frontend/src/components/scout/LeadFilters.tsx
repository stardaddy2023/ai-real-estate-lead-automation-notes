"use client"

import React, { useState } from 'react'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Button } from '@/components/ui/button'
import { Home, Sliders, AlertTriangle, Flame, X, RotateCcw } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'

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

// Hot List - Motivated Seller Signals from MLS/Homeharvest
export const HOT_LIST_TYPES = [
    "FSBO",
    "Price Reduced",
    "High Days on Market",
    "New Listing"
]

// ============================================
// Property Type Filter
// ============================================
interface PropertyTypeFilterProps {
    selectedPropertyTypes: string[]
    setSelectedPropertyTypes: (types: string[]) => void
}

export function PropertyTypeFilter({
    selectedPropertyTypes,
    setSelectedPropertyTypes
}: PropertyTypeFilterProps) {
    const [open, setOpen] = useState(false)

    const togglePropertyType = (type: string) => {
        if (selectedPropertyTypes.includes(type)) {
            setSelectedPropertyTypes(selectedPropertyTypes.filter(t => t !== type))
        } else {
            setSelectedPropertyTypes([...selectedPropertyTypes, type])
        }
    }

    const handleReset = () => {
        setSelectedPropertyTypes([])
    }

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 px-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 gap-1.5"
                >
                    <Home className="w-3.5 h-3.5" />
                    <span className="text-xs font-medium hidden sm:inline">Type</span>
                    {selectedPropertyTypes.length > 0 && (
                        <span className="bg-blue-600 text-white text-[10px] px-1.5 py-0.5 rounded-full min-w-[18px] text-center">
                            {selectedPropertyTypes.length}
                        </span>
                    )}
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[220px] p-0 bg-white dark:bg-gray-950 border-gray-200 dark:border-gray-800 shadow-xl" align="start">
                <div className="flex items-center justify-between p-3 border-b border-gray-100 dark:border-gray-800">
                    <h3 className="font-medium text-sm">Property Type</h3>
                    <div className="flex items-center gap-1">
                        {selectedPropertyTypes.length > 0 && (
                            <Button variant="ghost" size="sm" className="h-6 px-1.5 text-xs text-muted-foreground hover:text-foreground" onClick={handleReset}>
                                <RotateCcw className="w-3 h-3" />
                            </Button>
                        )}
                        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setOpen(false)}>
                            <X className="w-3.5 h-3.5" />
                        </Button>
                    </div>
                </div>
                <ScrollArea className="max-h-[300px] p-3">
                    <div className="space-y-2">
                        {PROPERTY_TYPES.map(type => (
                            <div key={type} className="flex items-center space-x-2">
                                <Checkbox
                                    id={`type-${type}`}
                                    checked={selectedPropertyTypes.includes(type)}
                                    onCheckedChange={() => togglePropertyType(type)}
                                />
                                <label
                                    htmlFor={`type-${type}`}
                                    className="text-sm leading-none cursor-pointer"
                                >
                                    {type}
                                </label>
                            </div>
                        ))}
                    </div>
                </ScrollArea>
            </PopoverContent>
        </Popover>
    )
}

// ============================================
// Property Details Filter
// ============================================
interface PropertyDetailsFilterProps {
    minBeds: string
    setMinBeds: (val: string) => void
    minBaths: string
    setMinBaths: (val: string) => void
    minSqft: string
    setMinSqft: (val: string) => void
}

export function PropertyDetailsFilter({
    minBeds,
    setMinBeds,
    minBaths,
    setMinBaths,
    minSqft,
    setMinSqft
}: PropertyDetailsFilterProps) {
    const [open, setOpen] = useState(false)

    const handleReset = () => {
        setMinBeds("")
        setMinBaths("")
        setMinSqft("")
    }

    const hasActiveFilters = minBeds || minBaths || minSqft
    const activeCount = [minBeds, minBaths, minSqft].filter(Boolean).length

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 px-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 gap-1.5"
                >
                    <Sliders className="w-3.5 h-3.5" />
                    <span className="text-xs font-medium hidden sm:inline">Details</span>
                    {activeCount > 0 && (
                        <span className="bg-blue-600 text-white text-[10px] px-1.5 py-0.5 rounded-full min-w-[18px] text-center">
                            {activeCount}
                        </span>
                    )}
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[200px] p-0 bg-white dark:bg-gray-950 border-gray-200 dark:border-gray-800 shadow-xl" align="start">
                <div className="flex items-center justify-between p-3 border-b border-gray-100 dark:border-gray-800">
                    <h3 className="font-medium text-sm">Property Details</h3>
                    <div className="flex items-center gap-1">
                        {hasActiveFilters && (
                            <Button variant="ghost" size="sm" className="h-6 px-1.5 text-xs text-muted-foreground hover:text-foreground" onClick={handleReset}>
                                <RotateCcw className="w-3 h-3" />
                            </Button>
                        )}
                        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setOpen(false)}>
                            <X className="w-3.5 h-3.5" />
                        </Button>
                    </div>
                </div>
                <div className="p-3 space-y-3">
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
                    <div className="space-y-1">
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
            </PopoverContent>
        </Popover>
    )
}

// ============================================
// Distress Flags Filter
// ============================================
interface DistressFlagsFilterProps {
    selectedDistressTypes: string[]
    setSelectedDistressTypes: (types: string[]) => void
}

export function DistressFlagsFilter({
    selectedDistressTypes,
    setSelectedDistressTypes
}: DistressFlagsFilterProps) {
    const [open, setOpen] = useState(false)

    const toggleDistressType = (type: string) => {
        if (selectedDistressTypes.includes(type)) {
            setSelectedDistressTypes(selectedDistressTypes.filter(t => t !== type))
        } else {
            setSelectedDistressTypes([...selectedDistressTypes, type])
        }
    }

    const handleReset = () => {
        setSelectedDistressTypes([])
    }

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 px-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 gap-1.5"
                >
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span className="text-xs font-medium hidden sm:inline">Distress</span>
                    {selectedDistressTypes.length > 0 && (
                        <span className="bg-red-600 text-white text-[10px] px-1.5 py-0.5 rounded-full min-w-[18px] text-center">
                            {selectedDistressTypes.length}
                        </span>
                    )}
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[220px] p-0 bg-white dark:bg-gray-950 border-gray-200 dark:border-gray-800 shadow-xl" align="start">
                <div className="flex items-center justify-between p-3 border-b border-gray-100 dark:border-gray-800">
                    <h3 className="font-medium text-sm">Distress Flags</h3>
                    <div className="flex items-center gap-1">
                        {selectedDistressTypes.length > 0 && (
                            <Button variant="ghost" size="sm" className="h-6 px-1.5 text-xs text-muted-foreground hover:text-foreground" onClick={handleReset}>
                                <RotateCcw className="w-3 h-3" />
                            </Button>
                        )}
                        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setOpen(false)}>
                            <X className="w-3.5 h-3.5" />
                        </Button>
                    </div>
                </div>
                <ScrollArea className="max-h-[300px] p-3">
                    <div className="space-y-2">
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
                                    className={`text-sm leading-none cursor-pointer ${DISABLED_DISTRESS_TYPES.includes(type) ? 'text-gray-400' : ''}`}
                                >
                                    {type}
                                </label>
                            </div>
                        ))}
                    </div>
                </ScrollArea>
            </PopoverContent>
        </Popover>
    )
}

// ============================================
// Hot List Filter (FSBO, Price Reduced, High DOM, New Listing)
// ============================================
interface HotListFilterProps {
    selectedHotList: string[]
    setSelectedHotList: (types: string[]) => void
}

export function HotListFilter({
    selectedHotList,
    setSelectedHotList
}: HotListFilterProps) {
    const [open, setOpen] = useState(false)

    const toggleHotListType = (type: string) => {
        if (selectedHotList.includes(type)) {
            setSelectedHotList(selectedHotList.filter(t => t !== type))
        } else {
            setSelectedHotList([...selectedHotList, type])
        }
    }

    const handleReset = () => {
        setSelectedHotList([])
    }

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 px-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 gap-1.5"
                >
                    <Flame className="w-3.5 h-3.5" />
                    <span className="text-xs font-medium hidden sm:inline">Hot</span>
                    {selectedHotList.length > 0 && (
                        <span className="bg-orange-500 text-white text-[10px] px-1.5 py-0.5 rounded-full min-w-[18px] text-center">
                            {selectedHotList.length}
                        </span>
                    )}
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[220px] p-0 bg-white dark:bg-gray-950 border-gray-200 dark:border-gray-800 shadow-xl" align="start">
                <div className="flex items-center justify-between p-3 border-b border-gray-100 dark:border-gray-800">
                    <h3 className="font-medium text-sm">Hot List</h3>
                    <div className="flex items-center gap-1">
                        {selectedHotList.length > 0 && (
                            <Button variant="ghost" size="sm" className="h-6 px-1.5 text-xs text-muted-foreground hover:text-foreground" onClick={handleReset}>
                                <RotateCcw className="w-3 h-3" />
                            </Button>
                        )}
                        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setOpen(false)}>
                            <X className="w-3.5 h-3.5" />
                        </Button>
                    </div>
                </div>
                <ScrollArea className="max-h-[300px] p-3">
                    <div className="space-y-2">
                        {HOT_LIST_TYPES.map(type => (
                            <div key={type} className="flex items-center space-x-2">
                                <Checkbox
                                    id={`hot-${type}`}
                                    checked={selectedHotList.includes(type)}
                                    onCheckedChange={() => toggleHotListType(type)}
                                />
                                <label
                                    htmlFor={`hot-${type}`}
                                    className="text-sm leading-none cursor-pointer"
                                >
                                    {type}
                                </label>
                            </div>
                        ))}
                    </div>
                </ScrollArea>
            </PopoverContent>
        </Popover>
    )
}

// ============================================
// Legacy LeadFilters (kept for backwards compatibility)
// ============================================
interface LeadFiltersProps {
    selectedPropertyTypes: string[]
    setSelectedPropertyTypes: (types: string[]) => void
    selectedDistressTypes: string[]
    setSelectedDistressTypes: (types: string[]) => void
    selectedHotList: string[]
    setSelectedHotList: (types: string[]) => void
    minBeds: string
    setMinBeds: (val: string) => void
    minBaths: string
    setMinBaths: (val: string) => void
    minSqft: string
    setMinSqft: (val: string) => void
    onSearch: () => void
}

export function LeadFilters(props: LeadFiltersProps) {
    // This is now a wrapper that renders the four separate filters
    return (
        <div className="flex items-center gap-1">
            <PropertyTypeFilter
                selectedPropertyTypes={props.selectedPropertyTypes}
                setSelectedPropertyTypes={props.setSelectedPropertyTypes}
            />
            <PropertyDetailsFilter
                minBeds={props.minBeds}
                setMinBeds={props.setMinBeds}
                minBaths={props.minBaths}
                setMinBaths={props.setMinBaths}
                minSqft={props.minSqft}
                setMinSqft={props.setMinSqft}
            />
            <DistressFlagsFilter
                selectedDistressTypes={props.selectedDistressTypes}
                setSelectedDistressTypes={props.setSelectedDistressTypes}
            />
            <HotListFilter
                selectedHotList={props.selectedHotList}
                setSelectedHotList={props.setSelectedHotList}
            />
        </div>
    )
}

