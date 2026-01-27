"use client"

import React, { useState } from 'react'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Button } from '@/components/ui/button'
import { Home, Sliders, AlertTriangle, Flame, X, RotateCcw } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { useToast } from '@/components/ui/use-toast'

// Property types with sub-types and Pima County parcel use codes
export const PROPERTY_TYPES_WITH_SUBTYPES: Record<string, { codes: string[], subtypes: { name: string, code: string }[] | null }> = {
    "Single Family": {
        codes: ["01", "87"],
        subtypes: [
            { name: "Urban Subdivided", code: "Urban Subdivided" },
            { name: "Urban Non-Subdivided", code: "Urban Non-Subdivided" },
            { name: "Rural Subdivided", code: "Rural Subdivided" },
            { name: "Rural Non-Subdivided", code: "Rural Non-Subdivided" },
            { name: "With Guest House / Affixed MH", code: "With Guest House / Affixed MH" }
        ]
    },
    "Multi-Family": {
        codes: ["03"],
        subtypes: [
            { name: "Duplex/Triplex/Fourplex", code: "Duplex/Triplex/Fourplex" },
            { name: "Apartments 5-24", code: "Apartments 5-24" },
            { name: "Apartments 25-99", code: "Apartments 25-99" },
            { name: "Apartments 100+", code: "Apartments 100+" }
        ]
    },
    "Mobile Homes": {
        codes: ["08"],
        subtypes: [
            { name: "Individual Mobile Home", code: "Individual Mobile Home" },
            { name: "Mobile Home Park", code: "Mobile Home Park" }
        ]
    },
    "Condo": {
        codes: ["07"],
        subtypes: null
    },
    "Vacant Land": {
        // Pima County 4-digit codes: 00XX where XX = 1Y=Residential, 2Y=Commercial, 3Y=Industrial
        // Using 3-digit prefixes for LIKE 'prefix%' matching
        codes: ["00"],  // All vacant land starts with 00
        subtypes: [
            { name: "Residential", code: "Residential" },   // Matches 0011, 0012, 0013, 0014
            { name: "Commercial", code: "Commercial" },    // Matches 0020, 0021, 0022, 0026
            { name: "Industrial", code: "Industrial" },    // Matches 0030, 0031, 0032
            { name: "Condo", code: "Condo" }          // Matches 0040, 0041
        ]
    },
    "Commercial": {
        codes: ["10", "11", "12", "13", "14", "15", "16", "17", "18", "19"],
        subtypes: [
            { name: "Office/Bank", code: "Office/Bank" },
            { name: "Retail/Store", code: "Retail/Store" },
            { name: "Auto/Service", code: "Auto/Service" },
            { name: "Restaurant", code: "Restaurant" },
            { name: "Hotel/Motel", code: "Hotel/Motel" }
        ]
    },
    "Industrial / Storage": {
        codes: ["20", "21", "22", "23", "24", "25"],
        subtypes: [
            { name: "Manufacturing", code: "Manufacturing" },
            { name: "Warehouse", code: "Warehouse" },
            { name: "Mining/Quarry", code: "Mining/Quarry" }
        ]
    },
    "Parking": {
        codes: ["17"],
        subtypes: null
    },
    "Partially Complete": {
        codes: ["93", "94"],
        subtypes: null
    },
    "Salvage / Teardown": {
        codes: ["95", "96"],
        subtypes: null
    },
    "Mixed Use": {
        codes: ["09"],
        subtypes: null
    }
}

// Simple array for backwards compatibility
export const PROPERTY_TYPES = Object.keys(PROPERTY_TYPES_WITH_SUBTYPES)
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
    "New Listing",
    "Path of Progress"  // Uses GIS spatial search, not Homeharvest
]

// Listing Status - MLS listing status filters
export const LISTING_STATUS_TYPES = [
    "For Sale",
    "Contingent",
    "Pending",
    "Under Contract",
    "Coming Soon",
    "Sold"
]

// ============================================
// Reusable Content Components
// ============================================

function PropertyTypeContent({
    selectedPropertyTypes,
    togglePropertyType,
    selectedSubTypes,
    toggleSubType
}: {
    selectedPropertyTypes: string[],
    togglePropertyType: (t: string) => void,
    selectedSubTypes?: string[],
    toggleSubType?: (subtype: string) => void
}) {
    return (
        <div className="space-y-2">
            {PROPERTY_TYPES.map(type => {
                const typeConfig = PROPERTY_TYPES_WITH_SUBTYPES[type]
                const isSelected = selectedPropertyTypes.includes(type)
                const hasSubtypes = typeConfig?.subtypes && typeConfig.subtypes.length > 0

                return (
                    <div key={type}>
                        <div className="flex items-center space-x-2">
                            <Checkbox
                                id={`type-${type}`}
                                checked={isSelected}
                                onCheckedChange={() => togglePropertyType(type)}
                            />
                            <label htmlFor={`type-${type}`} className="text-sm leading-none cursor-pointer text-gray-200">
                                {type}
                            </label>
                        </div>

                        {/* Sub-types appear indented when parent is selected */}
                        {hasSubtypes && isSelected && toggleSubType && selectedSubTypes && (
                            <div className="ml-6 mt-2 pl-2 border-l border-gray-700 space-y-1.5">
                                <p className="text-xs text-gray-500 mb-1">Filter by Sub-Type:</p>
                                {typeConfig.subtypes!.map(subtype => (
                                    <div key={subtype.code} className="flex items-center space-x-2">
                                        <Checkbox
                                            id={`subtype-${subtype.code}`}
                                            checked={selectedSubTypes.includes(subtype.code)}
                                            onCheckedChange={() => toggleSubType(subtype.code)}
                                        />
                                        <label htmlFor={`subtype-${subtype.code}`} className="text-xs leading-none cursor-pointer text-gray-300">
                                            {subtype.name}
                                        </label>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )
            })}
        </div>
    )
}

function PropertyDetailsContent({
    minBeds, setMinBeds, maxBeds, setMaxBeds,
    minBaths, setMinBaths, maxBaths, setMaxBaths,
    minSqft, setMinSqft, maxSqft, setMaxSqft,
    minYearBuilt, setMinYearBuilt, maxYearBuilt, setMaxYearBuilt,
    hasPool, setHasPool, hasGarage, setHasGarage, hasGuestHouse, setHasGuestHouse
}: PropertyDetailsFilterProps) {
    return (
        <div className="space-y-3">
            {/* Beds */}
            <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Beds</Label>
                <div className="flex gap-2">
                    <input
                        type="number"
                        className="w-full bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-900 dark:text-white"
                        value={minBeds}
                        onChange={(e) => setMinBeds(e.target.value)}
                        placeholder="Min"
                    />
                    <span className="text-gray-400 self-center">-</span>
                    <input
                        type="number"
                        className="w-full bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-900 dark:text-white"
                        value={maxBeds}
                        onChange={(e) => setMaxBeds(e.target.value)}
                        placeholder="Max"
                    />
                </div>
            </div>
            {/* Baths */}
            <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Baths</Label>
                <div className="flex gap-2">
                    <input
                        type="number"
                        className="w-full bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-900 dark:text-white"
                        value={minBaths}
                        onChange={(e) => setMinBaths(e.target.value)}
                        placeholder="Min"
                    />
                    <span className="text-gray-400 self-center">-</span>
                    <input
                        type="number"
                        className="w-full bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-900 dark:text-white"
                        value={maxBaths}
                        onChange={(e) => setMaxBaths(e.target.value)}
                        placeholder="Max"
                    />
                </div>
            </div>
            {/* SqFt */}
            <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Sqft</Label>
                <div className="flex gap-2">
                    <input
                        type="number"
                        className="w-full bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-900 dark:text-white"
                        value={minSqft}
                        onChange={(e) => setMinSqft(e.target.value)}
                        placeholder="Min"
                    />
                    <span className="text-gray-400 self-center">-</span>
                    <input
                        type="number"
                        className="w-full bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-900 dark:text-white"
                        value={maxSqft}
                        onChange={(e) => setMaxSqft(e.target.value)}
                        placeholder="Max"
                    />
                </div>
            </div>
            {/* Year Built */}
            <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Year Built</Label>
                <div className="flex gap-2">
                    <input
                        type="number"
                        className="w-full bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-900 dark:text-white"
                        value={minYearBuilt}
                        onChange={(e) => setMinYearBuilt(e.target.value)}
                        placeholder="Min"
                    />
                    <span className="text-gray-400 self-center">-</span>
                    <input
                        type="number"
                        className="w-full bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 text-gray-900 dark:text-white"
                        value={maxYearBuilt}
                        onChange={(e) => setMaxYearBuilt(e.target.value)}
                        placeholder="Max"
                    />
                </div>
            </div>
            {/* Property Features */}
            <div className="space-y-2 pt-2 border-t border-gray-700">
                <Label className="text-xs text-muted-foreground">Property Features</Label>
                <div className="flex flex-wrap gap-3">
                    <label className="flex items-center gap-2 cursor-pointer">
                        <Checkbox
                            checked={hasPool === true}
                            onCheckedChange={(checked) => setHasPool(checked ? true : null)}
                        />
                        <span className="text-sm text-white">🏊 Pool</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                        <Checkbox
                            checked={hasGarage === true}
                            onCheckedChange={(checked) => setHasGarage(checked ? true : null)}
                        />
                        <span className="text-sm text-white">🚗 Garage</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                        <Checkbox
                            checked={hasGuestHouse === true}
                            onCheckedChange={(checked) => setHasGuestHouse(checked ? true : null)}
                        />
                        <span className="text-sm text-white">🏠 Guest House</span>
                    </label>
                </div>
            </div>
        </div>
    )
}

function DistressFlagsContent({ selectedDistressTypes, toggleDistressType }: { selectedDistressTypes: string[], toggleDistressType: (t: string) => void }) {
    return (
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
                        className={`text-sm leading-none cursor-pointer ${DISABLED_DISTRESS_TYPES.includes(type) ? 'text-gray-500' : 'text-gray-200'}`}
                    >
                        {type}
                    </label>
                </div>
            ))}
        </div>
    )
}

function HotListContent({
    selectedHotList,
    toggleHotListType,
    selectedStatuses,
    toggleStatus
}: {
    selectedHotList: string[],
    toggleHotListType: (t: string) => void,
    selectedStatuses: string[],
    toggleStatus: (s: string) => void
}) {
    const isFsboSelected = selectedHotList.includes("FSBO")

    return (
        <div className="space-y-2">
            {HOT_LIST_TYPES.map(type => (
                <div key={type}>
                    <div className="flex items-center space-x-2">
                        <Checkbox
                            id={`hot-${type}`}
                            checked={selectedHotList.includes(type)}
                            onCheckedChange={() => toggleHotListType(type)}
                        />
                        <label htmlFor={`hot-${type}`} className="text-sm leading-none cursor-pointer text-gray-200">
                            {type}
                        </label>
                    </div>

                    {/* Status sub-options appear indented under FSBO when selected */}
                    {type === "FSBO" && isFsboSelected && (
                        <div className="ml-6 mt-2 pl-2 border-l border-gray-700 space-y-1.5">
                            <p className="text-xs text-gray-500 mb-1">Filter by Status:</p>
                            {LISTING_STATUS_TYPES.map(status => (
                                <div key={status} className="flex items-center space-x-2">
                                    <Checkbox
                                        id={`status-${status}`}
                                        checked={selectedStatuses.includes(status)}
                                        onCheckedChange={() => toggleStatus(status)}
                                    />
                                    <label htmlFor={`status-${status}`} className="text-xs leading-none cursor-pointer text-gray-300">
                                        {status}
                                    </label>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            ))}
        </div>
    )
}

function ListingStatusContent({ selectedStatuses, toggleStatus }: { selectedStatuses: string[], toggleStatus: (t: string) => void }) {
    return (
        <div className="space-y-2">
            {LISTING_STATUS_TYPES.map(status => (
                <div key={status} className="flex items-center space-x-2">
                    <Checkbox
                        id={`status-${status}`}
                        checked={selectedStatuses.includes(status)}
                        onCheckedChange={() => toggleStatus(status)}
                    />
                    <label htmlFor={`status-${status}`} className="text-sm leading-none cursor-pointer text-gray-200">
                        {status}
                    </label>
                </div>
            ))}
        </div>
    )
}

// ============================================
// Property Type Filter (Popover Wrapper)
// ============================================
interface PropertyTypeFilterProps {
    selectedPropertyTypes: string[]
    setSelectedPropertyTypes: (types: string[]) => void
    selectedSubTypes?: string[]
    setSelectedSubTypes?: (types: string[]) => void
}

export function PropertyTypeFilter({
    selectedPropertyTypes,
    setSelectedPropertyTypes,
    selectedSubTypes = [],
    setSelectedSubTypes
}: PropertyTypeFilterProps) {
    const [open, setOpen] = useState(false)

    const togglePropertyType = (type: string) => {
        if (selectedPropertyTypes.includes(type)) {
            setSelectedPropertyTypes(selectedPropertyTypes.filter(t => t !== type))
            // Also clear sub-types for this parent when unchecking
            if (setSelectedSubTypes) {
                const parentConfig = PROPERTY_TYPES_WITH_SUBTYPES[type]
                if (parentConfig?.subtypes) {
                    const parentSubtypeCodes = parentConfig.subtypes.map(s => s.code)
                    setSelectedSubTypes(selectedSubTypes.filter(s => !parentSubtypeCodes.includes(s)))
                }
            }
        } else {
            setSelectedPropertyTypes([...selectedPropertyTypes, type])
        }
    }

    const toggleSubType = (code: string) => {
        if (!setSelectedSubTypes) return
        if (selectedSubTypes.includes(code)) {
            setSelectedSubTypes(selectedSubTypes.filter(c => c !== code))
        } else {
            setSelectedSubTypes([...selectedSubTypes, code])
        }
    }

    const handleReset = () => {
        setSelectedPropertyTypes([])
        if (setSelectedSubTypes) setSelectedSubTypes([])
    }

    const totalSelected = selectedPropertyTypes.length + selectedSubTypes.length

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
                    {totalSelected > 0 && (
                        <span className="bg-blue-600 text-white text-[10px] px-1.5 py-0.5 rounded-full min-w-[18px] text-center">
                            {totalSelected}
                        </span>
                    )}
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[260px] p-0 bg-white dark:bg-gray-950 border-gray-200 dark:border-gray-800 shadow-xl" align="start">
                <div className="flex items-center justify-between p-3 border-b border-gray-100 dark:border-gray-800">
                    <h3 className="font-medium text-sm">Property Type</h3>
                    <div className="flex items-center gap-1">
                        {totalSelected > 0 && (
                            <Button variant="ghost" size="sm" className="h-6 px-1.5 text-xs text-muted-foreground hover:text-foreground" onClick={handleReset}>
                                <RotateCcw className="w-3 h-3" />
                            </Button>
                        )}
                        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setOpen(false)}>
                            <X className="w-3.5 h-3.5" />
                        </Button>
                    </div>
                </div>
                <ScrollArea className="max-h-[400px] p-3">
                    <PropertyTypeContent
                        selectedPropertyTypes={selectedPropertyTypes}
                        togglePropertyType={togglePropertyType}
                        selectedSubTypes={selectedSubTypes}
                        toggleSubType={toggleSubType}
                    />
                </ScrollArea>
            </PopoverContent>
        </Popover>
    )
}

// ============================================
// Property Details Filter (Popover Wrapper)
// ============================================
interface PropertyDetailsFilterProps {
    minBeds: string
    setMinBeds: (val: string) => void
    maxBeds: string
    setMaxBeds: (val: string) => void
    minBaths: string
    setMinBaths: (val: string) => void
    maxBaths: string
    setMaxBaths: (val: string) => void
    minSqft: string
    setMinSqft: (val: string) => void
    maxSqft: string
    setMaxSqft: (val: string) => void
    minYearBuilt: string
    setMinYearBuilt: (val: string) => void
    maxYearBuilt: string
    setMaxYearBuilt: (val: string) => void
    hasPool: boolean | null
    setHasPool: (val: boolean | null) => void
    hasGarage: boolean | null
    setHasGarage: (val: boolean | null) => void
    hasGuestHouse: boolean | null
    setHasGuestHouse: (val: boolean | null) => void
}

export function PropertyDetailsFilter(props: PropertyDetailsFilterProps) {
    const [open, setOpen] = useState(false)
    const {
        minBeds, setMinBeds, maxBeds, setMaxBeds,
        minBaths, setMinBaths, maxBaths, setMaxBaths,
        minSqft, setMinSqft, maxSqft, setMaxSqft,
        minYearBuilt, setMinYearBuilt, maxYearBuilt, setMaxYearBuilt,
        hasPool, setHasPool, hasGarage, setHasGarage, hasGuestHouse, setHasGuestHouse
    } = props

    const handleReset = () => {
        setMinBeds("")
        setMaxBeds("")
        setMinBaths("")
        setMaxBaths("")
        setMinSqft("")
        setMaxSqft("")
        setMinYearBuilt("")
        setMaxYearBuilt("")
        setHasPool(null)
        setHasGarage(null)
        setHasGuestHouse(null)
    }

    const hasActiveFilters = minBeds || maxBeds || minBaths || maxBaths || minSqft || maxSqft || minYearBuilt || maxYearBuilt || hasPool || hasGarage || hasGuestHouse
    const activeCount = [minBeds, maxBeds, minBaths, maxBaths, minSqft, maxSqft, minYearBuilt, maxYearBuilt, hasPool, hasGarage, hasGuestHouse].filter(Boolean).length

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
                <div className="p-3">
                    <PropertyDetailsContent {...props} />
                </div>
            </PopoverContent>
        </Popover>
    )
}

// ============================================
// Distress Flags Filter (Popover Wrapper)
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
                    <DistressFlagsContent selectedDistressTypes={selectedDistressTypes} toggleDistressType={toggleDistressType} />
                </ScrollArea>
            </PopoverContent>
        </Popover>
    )
}

// ============================================
// Hot List Filter (Popover Wrapper)
// ============================================
interface HotListFilterProps {
    selectedHotList: string[]
    setSelectedHotList: (types: string[]) => void
    selectedStatuses: string[]
    setSelectedStatuses: (statuses: string[]) => void
}

export function HotListFilter({
    selectedHotList,
    setSelectedHotList,
    selectedStatuses,
    setSelectedStatuses
}: HotListFilterProps) {
    const [open, setOpen] = useState(false)
    const { toast } = useToast()

    const toggleHotListType = (type: string) => {
        // 1. Handle Uncheck
        if (selectedHotList.includes(type)) {
            setSelectedHotList(selectedHotList.filter(t => t !== type))
            return
        }

        // 2. Handle Check (with Conflict Resolution)
        let newList = [...selectedHotList, type]

        // Define conflicts (Mutually Exclusive)
        const conflicts: Record<string, string> = {
            "New Listing": "High Days on Market",
            "High Days on Market": "New Listing"
        }

        const conflictType = conflicts[type]
        if (conflictType && newList.includes(conflictType)) {
            // Remove the OLD conflicting option, keep the NEW one
            newList = newList.filter(t => t !== conflictType)
            toast({
                title: "Filter Conflict Resolved",
                description: `Selected "${type}", removed conflicting "${conflictType}"`,
                variant: "default"
            })
        }

        setSelectedHotList(newList)
    }

    const handleReset = () => {
        setSelectedHotList([])
        setSelectedStatuses([])
    }

    const toggleStatus = (status: string) => {
        if (selectedStatuses.includes(status)) {
            setSelectedStatuses(selectedStatuses.filter(s => s !== status))
        } else {
            setSelectedStatuses([...selectedStatuses, status])
        }
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
                <ScrollArea className="max-h-[350px] p-3">
                    <HotListContent
                        selectedHotList={selectedHotList}
                        toggleHotListType={toggleHotListType}
                        selectedStatuses={selectedStatuses}
                        toggleStatus={toggleStatus}
                    />
                </ScrollArea>
            </PopoverContent>
        </Popover>
    )
}

// ============================================
// Listing Status Filter (Popover Wrapper)
// ============================================
interface ListingStatusFilterProps {
    selectedStatuses: string[]
    setSelectedStatuses: (statuses: string[]) => void
}

export function ListingStatusFilter({
    selectedStatuses,
    setSelectedStatuses
}: ListingStatusFilterProps) {
    const [open, setOpen] = useState(false)

    const toggleStatus = (status: string) => {
        if (selectedStatuses.includes(status)) {
            setSelectedStatuses(selectedStatuses.filter(s => s !== status))
        } else {
            setSelectedStatuses([...selectedStatuses, status])
        }
    }

    const handleReset = () => {
        setSelectedStatuses([])
    }

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 px-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 gap-1.5"
                >
                    <span className="text-xs">📋</span>
                    <span className="text-xs font-medium hidden sm:inline">Status</span>
                    {selectedStatuses.length > 0 && (
                        <span className="bg-cyan-600 text-white text-[10px] px-1.5 py-0.5 rounded-full min-w-[18px] text-center">
                            {selectedStatuses.length}
                        </span>
                    )}
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[200px] p-0 bg-white dark:bg-gray-950 border-gray-200 dark:border-gray-800 shadow-xl" align="start">
                <div className="flex items-center justify-between p-3 border-b border-gray-100 dark:border-gray-800">
                    <h3 className="font-medium text-sm">Listing Status</h3>
                    <div className="flex items-center gap-1">
                        {selectedStatuses.length > 0 && (
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
                    <ListingStatusContent selectedStatuses={selectedStatuses} toggleStatus={toggleStatus} />
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
    selectedPropertySubTypes?: string[]
    setSelectedPropertySubTypes?: (types: string[]) => void
    selectedDistressTypes: string[]
    setSelectedDistressTypes: (types: string[]) => void
    selectedHotList: string[]
    setSelectedHotList: (types: string[]) => void
    selectedStatuses: string[]
    setSelectedStatuses: (statuses: string[]) => void
    minBeds: string
    setMinBeds: (val: string) => void
    maxBeds: string
    setMaxBeds: (val: string) => void
    minBaths: string
    setMinBaths: (val: string) => void
    maxBaths: string
    setMaxBaths: (val: string) => void
    minSqft: string
    setMinSqft: (val: string) => void
    maxSqft: string
    setMaxSqft: (val: string) => void
    minYearBuilt: string
    setMinYearBuilt: (val: string) => void
    maxYearBuilt: string
    setMaxYearBuilt: (val: string) => void
    hasPool: boolean | null
    setHasPool: (val: boolean | null) => void
    hasGarage: boolean | null
    setHasGarage: (val: boolean | null) => void
    hasGuestHouse: boolean | null
    setHasGuestHouse: (val: boolean | null) => void
    onSearch: () => void
    mobile?: boolean
}

export function LeadFilters(props: LeadFiltersProps) {
    const { toast } = useToast() // Need toast for mobile HotList toggle logic

    // Helper for mobile toggles (since we don't have the internal state of the sub-components)
    const togglePropertyType = (type: string) => {
        if (props.selectedPropertyTypes.includes(type)) {
            props.setSelectedPropertyTypes(props.selectedPropertyTypes.filter(t => t !== type))
        } else {
            props.setSelectedPropertyTypes([...props.selectedPropertyTypes, type])
        }
    }

    const toggleDistressType = (type: string) => {
        if (props.selectedDistressTypes.includes(type)) {
            props.setSelectedDistressTypes(props.selectedDistressTypes.filter(t => t !== type))
        } else {
            props.setSelectedDistressTypes([...props.selectedDistressTypes, type])
        }
    }

    const toggleHotListType = (type: string) => {
        if (props.selectedHotList.includes(type)) {
            props.setSelectedHotList(props.selectedHotList.filter(t => t !== type))
            return
        }
        let newList = [...props.selectedHotList, type]
        const conflicts: Record<string, string> = { "New Listing": "High Days on Market", "High Days on Market": "New Listing" }
        const conflictType = conflicts[type]
        if (conflictType && newList.includes(conflictType)) {
            newList = newList.filter(t => t !== conflictType)
            toast({ title: "Filter Conflict Resolved", description: `Selected "${type}", removed conflicting "${conflictType}"`, variant: "default" })
        }
        props.setSelectedHotList(newList)
    }

    const toggleStatus = (status: string) => {
        if (props.selectedStatuses.includes(status)) {
            props.setSelectedStatuses(props.selectedStatuses.filter(s => s !== status))
        } else {
            props.setSelectedStatuses([...props.selectedStatuses, status])
        }
    }

    if (props.mobile) {
        return (
            <div className="flex flex-col gap-6">
                <div className="space-y-3">
                    <h3 className="font-semibold text-white flex items-center gap-2">
                        <Home className="w-4 h-4 text-blue-400" /> Property Type
                    </h3>
                    <div className="pl-2">
                        <PropertyTypeContent selectedPropertyTypes={props.selectedPropertyTypes} togglePropertyType={togglePropertyType} />
                    </div>
                </div>

                <div className="space-y-3">
                    <h3 className="font-semibold text-white flex items-center gap-2">
                        <Sliders className="w-4 h-4 text-green-400" /> Property Details
                    </h3>
                    <div className="pl-2">
                        <PropertyDetailsContent {...props} />
                    </div>
                </div>

                <div className="space-y-3">
                    <h3 className="font-semibold text-white flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-red-400" /> Distress Flags
                    </h3>
                    <div className="pl-2">
                        <DistressFlagsContent selectedDistressTypes={props.selectedDistressTypes} toggleDistressType={toggleDistressType} />
                    </div>
                </div>

                <div className="space-y-3">
                    <h3 className="font-semibold text-white flex items-center gap-2">
                        <Flame className="w-4 h-4 text-orange-400" /> Hot List
                    </h3>
                    <div className="pl-2">
                        <HotListContent
                            selectedHotList={props.selectedHotList}
                            toggleHotListType={toggleHotListType}
                            selectedStatuses={props.selectedStatuses}
                            toggleStatus={toggleStatus}
                        />
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="flex items-center gap-1">
            <PropertyTypeFilter
                selectedPropertyTypes={props.selectedPropertyTypes}
                setSelectedPropertyTypes={props.setSelectedPropertyTypes}
                selectedSubTypes={props.selectedPropertySubTypes}
                setSelectedSubTypes={props.setSelectedPropertySubTypes}
            />
            <PropertyDetailsFilter
                minBeds={props.minBeds}
                setMinBeds={props.setMinBeds}
                maxBeds={props.maxBeds}
                setMaxBeds={props.setMaxBeds}
                minBaths={props.minBaths}
                setMinBaths={props.setMinBaths}
                maxBaths={props.maxBaths}
                setMaxBaths={props.setMaxBaths}
                minSqft={props.minSqft}
                setMinSqft={props.setMinSqft}
                maxSqft={props.maxSqft}
                setMaxSqft={props.setMaxSqft}
                minYearBuilt={props.minYearBuilt}
                setMinYearBuilt={props.setMinYearBuilt}
                maxYearBuilt={props.maxYearBuilt}
                setMaxYearBuilt={props.setMaxYearBuilt}
                hasPool={props.hasPool}
                setHasPool={props.setHasPool}
                hasGarage={props.hasGarage}
                setHasGarage={props.setHasGarage}
                hasGuestHouse={props.hasGuestHouse}
                setHasGuestHouse={props.setHasGuestHouse}
            />
            <DistressFlagsFilter
                selectedDistressTypes={props.selectedDistressTypes}
                setSelectedDistressTypes={props.setSelectedDistressTypes}
            />
            <HotListFilter
                selectedHotList={props.selectedHotList}
                setSelectedHotList={props.setSelectedHotList}
                selectedStatuses={props.selectedStatuses}
                setSelectedStatuses={props.setSelectedStatuses}
            />
        </div>
    )
}

