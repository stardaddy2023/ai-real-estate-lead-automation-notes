"use client"

import React from 'react'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/simple-accordion'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Label } from '@/components/ui/label'
import { Info } from 'lucide-react'
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
            { id: 'home_value', label: 'Home Value' },
            { id: 'inventory', label: 'Inventory' },
            { id: 'days_on_market', label: 'Days on Market' },
        ]
    },
    {
        id: 'trends',
        label: 'Market Trends',
        items: [
            { id: 'price_drops', label: 'Price Drops' },
            { id: 'new_listings', label: 'New Listings' },
            { id: 'sales_count', label: 'Home Sales' },
        ]
    },
    {
        id: 'investor',
        label: 'Investor Metrics',
        items: [
            { id: 'rental_yield', label: 'Rental Yield' },
            { id: 'cap_rate', label: 'Cap Rate' },
            { id: 'rent_price', label: 'Rent Price' },
        ]
    }
]

export function MarketSidebar({ activeLayer, onLayerChange }: MarketSidebarProps) {
    return (
        <div className="w-64 bg-white dark:bg-gray-950 border-r border-gray-200 dark:border-gray-800 h-full flex flex-col overflow-y-auto z-20">
            <div className="p-4 border-b border-gray-200 dark:border-gray-800">
                <h2 className="font-bold text-lg flex items-center gap-2">
                    <span className="text-foreground">Data Layers</span>
                </h2>
            </div>

            <div className="p-2">
                <Accordion type="multiple" defaultValue={['popular', 'trends']} className="w-full">
                    {CATEGORIES.map(category => (
                        <AccordionItem key={category.id} value={category.id} className="border-b-0 mb-1">
                            <AccordionTrigger className="px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-900 rounded-md text-sm font-medium">
                                {category.label}
                            </AccordionTrigger>
                            <AccordionContent>
                                <div className="pl-2 pr-2 pb-2 space-y-1">
                                    {category.items.map(item => (
                                        <div
                                            key={item.id}
                                            onClick={() => onLayerChange(item.id as DataLayerType)}
                                            className={`flex items-center justify-between px-3 py-2 rounded-md cursor-pointer transition-colors ${activeLayer === item.id ? 'bg-blue-50 dark:bg-blue-900/20' : 'hover:bg-gray-50 dark:hover:bg-gray-900/50'}`}
                                        >
                                            <div className="flex items-center gap-3">
                                                <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${activeLayer === item.id ? 'border-blue-500' : 'border-gray-300 dark:border-gray-600'}`}>
                                                    {activeLayer === item.id && <div className="w-2 h-2 rounded-full bg-blue-500" />}
                                                </div>
                                                <span className={`text-sm ${activeLayer === item.id ? 'text-blue-600 dark:text-blue-400 font-medium' : 'text-gray-600 dark:text-gray-400'}`}>
                                                    {item.label}
                                                </span>
                                            </div>
                                            <Info className="w-3 h-3 text-gray-300 hover:text-gray-500" />
                                        </div>
                                    ))}
                                </div>
                            </AccordionContent>
                        </AccordionItem>
                    ))}
                </Accordion>
            </div>

            <div className="mt-auto p-4 border-t border-gray-200 dark:border-gray-800">
                <button className="w-full text-left text-xs text-red-500 font-medium hover:underline flex items-center gap-1">
                    Explore Data Points &rarr;
                </button>
            </div>
        </div>
    )
}
