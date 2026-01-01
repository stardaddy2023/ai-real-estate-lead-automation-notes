"use client"

import React, { useState } from 'react'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { Filter, X } from 'lucide-react'

export function MarketFilters() {
    const [populationRange, setPopulationRange] = useState([0, 50000])
    const [homeValueRange, setHomeValueRange] = useState([100000, 1000000])

    return (
        <Popover>
            <PopoverTrigger asChild>
                <Button variant="outline" className="h-9 bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 gap-2">
                    <Filter className="w-4 h-4" />
                    Filters
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-80 p-4 bg-white dark:bg-gray-950 border-gray-200 dark:border-gray-800 shadow-xl" align="end">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-lg">Filters</h3>
                    <X className="w-4 h-4 cursor-pointer opacity-50 hover:opacity-100" />
                </div>

                <div className="space-y-6">
                    {/* Population Filter */}
                    <div className="space-y-3">
                        <div className="flex justify-between text-sm">
                            <span className="font-medium">Population</span>
                            <span className="text-gray-500 text-xs">{populationRange[0].toLocaleString()} - {populationRange[1].toLocaleString()}</span>
                        </div>
                        <Slider
                            defaultValue={[0, 50000]}
                            max={100000}
                            step={1000}
                            value={populationRange}
                            onValueChange={setPopulationRange}
                            className="py-2"
                        />
                    </div>

                    {/* Home Value Filter */}
                    <div className="space-y-3">
                        <div className="flex justify-between text-sm">
                            <span className="font-medium">Home Value</span>
                            <span className="text-gray-500 text-xs">${(homeValueRange[0] / 1000).toFixed(0)}k - ${(homeValueRange[1] / 1000).toFixed(0)}k</span>
                        </div>
                        <Slider
                            defaultValue={[100000, 1000000]}
                            max={2000000}
                            step={10000}
                            value={homeValueRange}
                            onValueChange={setHomeValueRange}
                            className="py-2"
                        />
                    </div>

                    {/* Buttons */}
                    <div className="pt-2 flex gap-2">
                        <Button variant="outline" className="flex-1 h-8 text-xs" onClick={() => {
                            setPopulationRange([0, 50000])
                            setHomeValueRange([100000, 1000000])
                        }}>
                            Reset
                        </Button>
                        <Button className="flex-1 h-8 text-xs bg-red-500 hover:bg-red-600 text-white">
                            Apply Filters
                        </Button>
                    </div>
                </div>
            </PopoverContent>
        </Popover>
    )
}
