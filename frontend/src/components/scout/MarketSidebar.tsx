"use client"

import React, { useState } from 'react'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/simple-accordion'
import { Button } from '@/components/ui/button'
import { Info, ChevronLeft, ChevronRight, Layers } from 'lucide-react'
import { DataLayerType } from './MarketMap'

interface MarketSidebarProps {
    activeLayer: DataLayerType
    onLayerChange: (layer: DataLayerType) => void
}

const CATEGORIES = [
    {
        id: 'popular',
        label: 'Popular Data',
        items: [
            { id: 'home_value', label: 'Home Value', source: 'Zillow' },
            { id: 'home_value_growth_yoy', label: 'Home Value Growth (YoY)', source: 'Zillow' },
            { id: 'inventory', label: 'For Sale Inventory', source: 'Realtor.com' },
            { id: 'days_on_market', label: 'Days on Market', source: 'Realtor.com' },
        ]
    },
    {
        id: 'trends',
        label: 'Market Trends',
        items: [
            { id: 'price_drops', label: 'Price Drops', source: 'Realtor.com' },
            { id: 'new_listings', label: 'New Listings', source: 'Realtor.com' },
            { id: 'home_sales', label: 'Home Sales', source: 'Redfin' },
            { id: 'price_forecast', label: 'Home Price Forecast', source: 'Altos' },
        ]
    },
    {
        id: 'investor',
        label: 'Investor Metrics',
        items: [
            { id: 'cap_rate', label: 'Cap Rate', source: 'Internal' },
            { id: 'rental_yield', label: 'Rental Yield', source: 'Internal' },
            { id: 'rent_price', label: 'Rent Price', source: 'Zillow' },
            { id: 'overvalued_pct', label: 'Overvalued %', source: 'Internal' },
        ]
    },
    {
        id: 'demographics',
        label: 'Demographics',
        items: [
            { id: 'population_growth', label: 'Population Growth', source: 'Census' },
            { id: 'migration', label: 'Migration', source: 'Census' },
            { id: 'income', label: 'Household Income', source: 'Census' },
        ]
    }
]

export function MarketSidebar({ activeLayer, onLayerChange }: MarketSidebarProps) {
    const [isOpen, setIsOpen] = useState(false)

    return (
        <div className={`absolute top-20 right-4 z-10 transition-all duration-300 ease-in-out flex flex-col items-end ${isOpen ? 'w-72' : 'w-10'}`}>

            {/* Header / Toggle */}
            <div
                className={`bg-black text-white flex items-center justify-between p-2 shadow-lg border border-gray-800 cursor-pointer transition-all ${isOpen ? 'w-full rounded-t-lg' : 'w-10 h-10 rounded-full justify-center'
                    }`}
                onClick={() => setIsOpen(!isOpen)}
            >
                {isOpen ? (
                    <>
                        <span className="font-bold text-sm tracking-wide ml-2">DATA LAYERS</span>
                        <ChevronRight className="w-4 h-4" />
                    </>
                ) : (
                    <Layers className="w-5 h-5" />
                )}
            </div>

            {/* Content Panel */}
            {isOpen && (
                <div className="w-full bg-black/90 backdrop-blur-md border-x border-b border-gray-800 rounded-b-lg shadow-xl max-h-[calc(100vh-200px)] overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent animate-in slide-in-from-right-5">
                    <Accordion type="multiple" defaultValue={['popular', 'trends']} className="w-full">
                        {CATEGORIES.map(category => (
                            <AccordionItem key={category.id} value={category.id} className="border-b border-gray-800 last:border-0">
                                <AccordionTrigger className="px-4 py-3 hover:bg-white/5 text-gray-200 text-xs font-semibold uppercase tracking-wider">
                                    {category.label}
                                </AccordionTrigger>
                                <AccordionContent>
                                    <div className="px-2 pb-2 space-y-1">
                                        {category.items.map(item => (
                                            <div
                                                key={item.id}
                                                onClick={() => onLayerChange(item.id as DataLayerType)}
                                                className={`group flex items-center justify-between px-3 py-2 rounded cursor-pointer transition-all ${activeLayer === item.id
                                                    ? 'bg-blue-600/20 border border-blue-500/30'
                                                    : 'hover:bg-white/10 border border-transparent'
                                                    }`}
                                            >
                                                <div className="flex items-center gap-3">
                                                    <div className={`w-4 h-4 rounded-full border flex items-center justify-center shrink-0 ${activeLayer === item.id ? 'border-blue-500' : 'border-gray-500 group-hover:border-gray-300'
                                                        }`}>
                                                        {activeLayer === item.id && <div className="w-2 h-2 rounded-full bg-blue-500" />}
                                                    </div>
                                                    <div className="flex flex-col">
                                                        <span className={`text-sm ${activeLayer === item.id ? 'text-blue-400 font-medium' : 'text-gray-300 group-hover:text-white'}`}>
                                                            {item.label}
                                                        </span>
                                                    </div>
                                                </div>
                                                <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                                                    <Info className="w-3 h-3 text-gray-500 hover:text-gray-300" />
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </AccordionContent>
                            </AccordionItem>
                        ))}
                    </Accordion>
                </div>
            )}
        </div>
    )
}
