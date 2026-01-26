"use client"

import React, { useState } from 'react'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { Filter, X, PlusCircle, RotateCcw } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'

export function MarketFilters() {
    const [open, setOpen] = useState(false)

    // 1. Home Value ($0 - $2M)
    const [homeValueRange, setHomeValueRange] = useState([0, 2000000])
    // 2. Home Price Forecast (-20% - +20%)
    const [forecastRange, setForecastRange] = useState([-20, 20])
    // 3. Home Value Growth YoY (-20% - +20%)
    const [growthRange, setGrowthRange] = useState([-20, 20])
    // 4. Overvalued % (-50% - +50%)
    const [overvaluedRange, setOvervaluedRange] = useState([-50, 50])
    // 5. Population Growth (-10% - +10%)
    const [popGrowthRange, setPopGrowthRange] = useState([-10, 10])
    // 6. Price Cut % (0% - 50%)
    const [priceCutRange, setPriceCutRange] = useState([0, 50])
    // 7. Sale Inventory Growth YoY (-100% - +200%)
    const [inventoryGrowthRange, setInventoryGrowthRange] = useState([-100, 200])
    // 8. Median Household Income ($0 - $200k)
    const [incomeRange, setIncomeRange] = useState([0, 200000])

    const handleReset = () => {
        setHomeValueRange([0, 2000000])
        setForecastRange([-20, 20])
        setGrowthRange([-20, 20])
        setOvervaluedRange([-50, 50])
        setPopGrowthRange([-10, 10])
        setPriceCutRange([0, 50])
        setInventoryGrowthRange([-100, 200])
        setIncomeRange([0, 200000])
    }

    const formatCurrency = (val: number) => {
        if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`
        if (val >= 1000) return `$${(val / 1000).toFixed(0)}k`
        return `$${val}`
    }

    const formatPercent = (val: number) => `${val}%`

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button variant="outline" className="h-10 bg-white dark:bg-gray-950 border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 gap-2 shadow-lg">
                    <Filter className="w-4 h-4" />
                    <span className="hidden sm:inline">Filter</span>
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[400px] p-0 bg-white dark:bg-gray-950 border-gray-200 dark:border-gray-800 shadow-xl" align="end">
                <div className="flex items-center justify-between p-4 border-b border-gray-100 dark:border-gray-800">
                    <h3 className="font-semibold text-lg flex items-center gap-2">
                        Filters <span className="text-yellow-500">😎</span>
                    </h3>
                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setOpen(false)}>
                        <X className="w-4 h-4" />
                    </Button>
                </div>

                <div className="p-3 flex gap-2 overflow-x-auto border-b border-gray-100 dark:border-gray-800 scrollbar-hide">
                    {/* Quick Filters (Chips) */}
                    {['Cheapest', 'Most Expensive', 'Affordable', 'High Income', 'Most Overvalued'].map(chip => (
                        <div key={chip} className="px-3 py-1 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-xs font-medium rounded-full whitespace-nowrap cursor-pointer hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors">
                            {chip}
                        </div>
                    ))}
                </div>

                <ScrollArea className="h-[500px] p-4">
                    <div className="space-y-6 pr-4">

                        <FilterItem
                            label="Home Value"
                            range={homeValueRange}
                            setRange={setHomeValueRange}
                            min={0} max={2000000} step={10000}
                            format={formatCurrency}
                            onRemove={() => { }}
                        />

                        <FilterItem
                            label="Home Price Forecast (%)"
                            range={forecastRange}
                            setRange={setForecastRange}
                            min={-20} max={20} step={1}
                            format={formatPercent}
                            onRemove={() => { }}
                        />

                        <FilterItem
                            label="Home Value Growth (YoY)"
                            range={growthRange}
                            setRange={setGrowthRange}
                            min={-20} max={20} step={1}
                            format={formatPercent}
                            onRemove={() => { }}
                        />

                        <FilterItem
                            label="Overvalued %"
                            range={overvaluedRange}
                            setRange={setOvervaluedRange}
                            min={-50} max={50} step={1}
                            format={formatPercent}
                            onRemove={() => { }}
                        />

                        <FilterItem
                            label="Population Growth"
                            range={popGrowthRange}
                            setRange={setPopGrowthRange}
                            min={-10} max={10} step={0.1}
                            format={formatPercent}
                            onRemove={() => { }}
                        />

                        <Button variant="outline" className="w-full border-dashed text-red-500 border-red-200 hover:bg-red-50 dark:hover:bg-red-900/20 gap-2">
                            <PlusCircle className="w-4 h-4" /> Add data filters
                        </Button>

                    </div>
                </ScrollArea>

                <div className="p-4 border-t border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/50 flex gap-3">
                    <Button variant="outline" className="flex-1 border-red-200 text-red-500 hover:bg-red-50 hover:text-red-600" onClick={handleReset}>
                        Reset
                    </Button>
                    {/* Note: In a real app, this would apply the filters. For now it just closes. */}
                    <Button className="flex-1 bg-red-500 hover:bg-red-600 text-white" onClick={() => setOpen(false)}>
                        Apply Filters
                    </Button>
                </div>
            </PopoverContent>
        </Popover>
    )
}

interface FilterItemProps {
    label: string
    range: number[]
    setRange: (val: number[]) => void
    min: number
    max: number
    step: number
    format: (val: number) => string
    onRemove: () => void
}

function FilterItem({ label, range, setRange, min, max, step, format, onRemove }: FilterItemProps) {
    return (
        <div className="space-y-3">
            <div className="flex justify-between items-center">
                <span className="font-medium text-sm text-gray-700 dark:text-gray-200">{label}</span>
                <X
                    className="w-3 h-3 text-gray-400 cursor-pointer hover:text-red-500 transition-colors"
                    onClick={onRemove}
                />
            </div>

            {/* Custom Styled Slider */}
            <Slider
                defaultValue={[min, max]}
                min={min}
                max={max}
                step={step}
                value={range}
                onValueChange={setRange}
                className="py-2"
            // Note: We're using the default shadcn slider but we'd customize the track color in global css or via class overrides if needed.
            // For now, assuming the theme handles the primary color (which we might want to force to red for this component).
            />

            <div className="flex justify-between text-xs text-gray-500 font-medium">
                <div className="px-3 py-1 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 shadow-sm min-w-[60px] text-center">
                    {format(range[0])}
                </div>
                <div className="px-3 py-1 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 shadow-sm min-w-[60px] text-center">
                    {format(range[1])}
                </div>
            </div>
        </div>
    )
}
