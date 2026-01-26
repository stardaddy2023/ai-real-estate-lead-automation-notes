"use client"

import React, { useState } from 'react'
import dynamic from 'next/dynamic'
import { Search, Share2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DataLayerType, ViewMode } from './MarketMap'
import { MarketSidebar } from './MarketSidebar'
import { MarketFilters } from './MarketFilters'
import { MarketDetailPanel } from './MarketDetailPanel'
import { MarketBottomControls } from './MarketBottomControls'

// Dynamic import for Map to avoid SSR issues
const MarketMap = dynamic(() => import('./MarketMap').then(mod => mod.MarketMap), {
    ssr: false,
    loading: () => <div className="w-full h-full bg-gray-900 animate-pulse flex items-center justify-center text-gray-500">Loading Market Map...</div>
})

export default function MarketRecon() {
    // State
    const [activeLayer, setActiveLayer] = useState<DataLayerType>('home_value')
    const [viewMode, setViewMode] = useState<ViewMode>('zip')
    const [selectedRegion, setSelectedRegion] = useState<{ id: string; data: any } | null>(null)

    // Bottom Controls State
    const [tooltipEnabled, setTooltipEnabled] = useState(true)
    const [tableViewEnabled, setTableViewEnabled] = useState(false)
    const [selectedDate, setSelectedDate] = useState("Dec 2025")

    const handleRegionClick = (regionId: string, data: any) => {
        setSelectedRegion({ id: regionId, data })
    }

    return (
        <div className="flex h-screen w-full bg-black text-white overflow-hidden relative">

            {/* MAIN CONTENT - FULL SCREEN MAP */}
            <div className="flex-1 relative h-full flex flex-col">

                {/* TOP FLOATING BAR (Unified Layout) */}
                <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 w-full max-w-4xl px-4 pointer-events-none">
                    <div className="pointer-events-auto flex items-center justify-center w-full">

                        <div className="flex bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-md shadow-lg items-center px-3 h-10 gap-2 w-full md:w-auto">

                            {/* Search Input */}
                            <Search className="text-gray-400 w-4 h-4 shrink-0" />
                            <div className="flex-1 min-w-[200px] h-full">
                                <input
                                    type="text"
                                    placeholder="Search Zip Code, City, or Neighborhood..."
                                    className="bg-transparent border-none focus:ring-0 text-gray-900 dark:text-white placeholder:text-gray-400 h-full w-full focus:outline-none text-sm px-0"
                                />
                            </div>

                            <div className="h-4 w-px bg-gray-200 dark:bg-gray-800 mx-1" />

                            {/* View Mode Toggles */}
                            <div className="flex items-center gap-1">
                                {(['national', 'state', 'metro', 'county', 'zip'] as ViewMode[]).map((mode) => (
                                    <button
                                        key={mode}
                                        onClick={() => setViewMode(mode)}
                                        className={`px-2 py-1 text-xs font-medium rounded transition-colors capitalize ${viewMode === mode
                                                ? 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white'
                                                : 'text-gray-500 hover:text-gray-900 dark:hover:text-gray-300'
                                            }`}
                                    >
                                        {mode}
                                    </button>
                                ))}
                            </div>

                            <div className="h-4 w-px bg-gray-200 dark:bg-gray-800 mx-1" />

                            {/* Filters Button */}
                            <MarketFilters />

                            <div className="h-4 w-px bg-gray-200 dark:bg-gray-800 mx-1" />

                            {/* Share Button */}
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-500 hover:text-gray-900 dark:hover:text-gray-300">
                                <Share2 className="w-4 h-4" />
                            </Button>

                        </div>

                    </div>
                </div>

                {/* RIGHT SIDEBAR (Mini Menu) */}
                <MarketSidebar activeLayer={activeLayer} onLayerChange={setActiveLayer} />

                {/* MAP */}
                <div className="flex-1 relative z-0">
                    <MarketMap
                        activeLayer={activeLayer}
                        viewMode={viewMode}
                        tooltipEnabled={tooltipEnabled}
                        onRegionClick={handleRegionClick}
                    />
                </div>

                {/* BOTTOM CONTROLS */}
                <MarketBottomControls
                    tooltipEnabled={tooltipEnabled}
                    onTooltipChange={setTooltipEnabled}
                    tableViewEnabled={tableViewEnabled}
                    onTableViewChange={setTableViewEnabled}
                    selectedDate={selectedDate}
                    onDateChange={setSelectedDate}
                />

                {/* TABLE VIEW PANEL (Bottom Sheet) */}
                {tableViewEnabled && (
                    <div className="absolute bottom-20 left-4 right-4 h-64 bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg shadow-2xl z-20 p-4 animate-in slide-in-from-bottom-10">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="font-semibold text-sm">Table View: {activeLayer.replace(/_/g, ' ').toUpperCase()}</h3>
                            <Button variant="ghost" size="sm" onClick={() => setTableViewEnabled(false)}>Close</Button>
                        </div>
                        <div className="h-full flex items-center justify-center text-gray-500 text-sm">
                            Table data for {viewMode} view would appear here.
                        </div>
                    </div>
                )}

                {/* DETAIL PANEL OVERLAY */}
                {selectedRegion && (
                    <MarketDetailPanel
                        regionId={selectedRegion.id}
                        data={selectedRegion.data}
                        onClose={() => setSelectedRegion(null)}
                    />
                )}

            </div>
        </div>
    )
}
