"use client"

import React, { useState } from 'react'
import dynamic from 'next/dynamic'
import { Search, Share2, Download, Layers } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DataLayerType } from './MarketMap'
import { MarketSidebar } from './MarketSidebar'
import { MarketFilters } from './MarketFilters'
import { MarketTimeSlider } from './MarketTimeSlider'
import { MarketDetailPanel } from './MarketDetailPanel'
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"

// Dynamic import for Map to avoid SSR issues
const MarketMap = dynamic(() => import('./MarketMap').then(mod => mod.MarketMap), {
    ssr: false,
    loading: () => <div className="w-full h-full bg-gray-900 animate-pulse flex items-center justify-center text-gray-500">Loading Market Map...</div>
})

export default function MarketRecon() {
    const [activeLayer, setActiveLayer] = useState<DataLayerType>('home_value')
    const [selectedRegion, setSelectedRegion] = useState<{ id: string; data: any } | null>(null)
    const [isLayerDrawerOpen, setIsLayerDrawerOpen] = useState(false)

    const handleRegionClick = (regionId: string, data: any) => {
        setSelectedRegion({ id: regionId, data })
    }

    return (
        <div className="flex h-screen w-full bg-white dark:bg-black text-gray-900 dark:text-white overflow-hidden relative">

            {/* MAIN CONTENT - FULL SCREEN */}
            <div className="flex-1 relative h-full flex flex-col">

                {/* TOP LEFT CONTROLS */}
                <div className="absolute top-4 left-4 z-20 flex items-center gap-3 pointer-events-none">

                    {/* Data Layers (Mini Menu) - LEFT SIDE */}
                    <div className="pointer-events-auto">
                        <Sheet open={isLayerDrawerOpen} onOpenChange={setIsLayerDrawerOpen}>
                            <SheetTrigger asChild>
                                <Button variant="outline" className="bg-white dark:bg-gray-950 border-gray-200 dark:border-gray-800 shadow-lg gap-2">
                                    <Layers className="w-4 h-4" />
                                    <span className="hidden sm:inline">Layers</span>
                                </Button>
                            </SheetTrigger>
                            <SheetContent side="left" className="p-0 w-80 border-r">
                                <MarketSidebar activeLayer={activeLayer} onLayerChange={setActiveLayer} />
                            </SheetContent>
                        </Sheet>
                    </div>

                    {/* Search */}
                    <div className="pointer-events-auto w-80 sm:w-96 bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-md shadow-lg flex items-center px-3 h-10">
                        <Search className="text-gray-400 w-4 h-4 mr-2" />
                        <input
                            type="text"
                            placeholder="Search your County, City, or ZIP Code"
                            className="flex-1 bg-transparent border-none focus:ring-0 text-sm placeholder:text-gray-400 h-full focus:outline-none"
                        />
                    </div>
                </div>

                {/* TOP RIGHT CONTROLS */}
                <div className="absolute top-4 right-4 z-20 flex items-center gap-3 pointer-events-none">

                    {/* Filters */}
                    <div className="pointer-events-auto flex items-center gap-2">
                        <div className="bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-md shadow-lg p-1 flex items-center gap-4 px-4 h-10 text-sm font-medium hidden md:flex">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input type="radio" name="scope" className="text-blue-600" />
                                <span>National</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input type="radio" name="scope" className="text-blue-600" />
                                <span>State</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input type="radio" name="scope" className="text-blue-600" />
                                <span>County</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input type="radio" name="scope" className="text-blue-600" defaultChecked />
                                <span>Zip</span>
                            </label>
                        </div>

                        <div className="pointer-events-auto">
                            <MarketFilters />
                        </div>

                        <div className="pointer-events-auto">
                            <Button variant="outline" size="icon" className="h-10 w-10 bg-white dark:bg-gray-950 border-gray-200 dark:border-gray-800 shadow-lg">
                                <Share2 className="w-4 h-4" />
                            </Button>
                        </div>
                    </div>


                </div>

                {/* MAP */}
                <div className="flex-1 relative z-0">
                    <MarketMap activeLayer={activeLayer} onRegionClick={handleRegionClick} />
                </div>

                {/* BOTTOM TIME SLIDER */}
                <MarketTimeSlider />

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
