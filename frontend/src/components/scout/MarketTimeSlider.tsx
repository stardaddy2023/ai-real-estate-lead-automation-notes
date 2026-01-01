"use client"

import React, { useState } from 'react'
import { Slider } from '@/components/ui/slider'
import { Play, Pause } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function MarketTimeSlider() {
    const [year, setYear] = useState([2025])
    const [isPlaying, setIsPlaying] = useState(false)

    return (
        <div className="absolute bottom-0 left-0 right-0 h-16 bg-white dark:bg-gray-950 border-t border-gray-200 dark:border-gray-800 flex items-center px-6 z-30">
            <div className="flex items-center gap-4 w-full max-w-4xl mx-auto">
                <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 rounded-full bg-red-500 hover:bg-red-600 text-white"
                    onClick={() => setIsPlaying(!isPlaying)}
                >
                    {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current ml-0.5" />}
                </Button>

                <div className="flex-1 relative pt-5 pb-2">
                    {/* Year Labels */}
                    <div className="absolute top-0 left-0 right-0 flex justify-between text-[10px] text-gray-400 font-medium px-1">
                        <span>2005</span>
                        <span>2010</span>
                        <span>2015</span>
                        <span>2020</span>
                        <span>2025</span>
                    </div>

                    <Slider
                        defaultValue={[2025]}
                        max={2025}
                        min={2005}
                        step={1}
                        value={year}
                        onValueChange={setYear}
                        className="cursor-pointer"
                    />
                </div>

                <div className="w-16 text-center font-bold text-lg text-gray-800 dark:text-gray-200">
                    {year[0]}
                </div>
            </div>
        </div>
    )
}
