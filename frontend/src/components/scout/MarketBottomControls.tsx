"use client"

import React from 'react'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Calendar, Table as TableIcon, Info } from 'lucide-react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface MarketBottomControlsProps {
    tooltipEnabled: boolean
    onTooltipChange: (enabled: boolean) => void
    tableViewEnabled: boolean
    onTableViewChange: (enabled: boolean) => void
    selectedDate: string
    onDateChange: (date: string) => void
}

export function MarketBottomControls({
    tooltipEnabled,
    onTooltipChange,
    tableViewEnabled,
    onTableViewChange,
    selectedDate,
    onDateChange
}: MarketBottomControlsProps) {
    return (
        <div className="absolute bottom-8 left-4 z-20 flex items-center gap-3">
            {/* Tooltip Toggle */}
            <div className="bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-full shadow-lg px-4 h-10 flex items-center gap-2">
                <Switch
                    id="tooltip-mode"
                    checked={tooltipEnabled}
                    onCheckedChange={onTooltipChange}
                    className="data-[state=checked]:bg-red-500"
                />
                <Label htmlFor="tooltip-mode" className="text-sm font-medium cursor-pointer">
                    Tooltip
                </Label>
            </div>

            {/* Table View Toggle */}
            <Button
                variant={tableViewEnabled ? "default" : "outline"}
                onClick={() => onTableViewChange(!tableViewEnabled)}
                className={`h-10 rounded-full shadow-lg gap-2 border-gray-200 dark:border-gray-800 ${tableViewEnabled
                    ? 'bg-white dark:bg-gray-950 text-foreground border-gray-300 dark:border-gray-700 ring-2 ring-gray-200 dark:ring-gray-800'
                    : 'bg-white dark:bg-gray-950 text-foreground'
                    }`}
            >
                <TableIcon className="w-4 h-4" />
                <span>Table View</span>
            </Button>

            {/* Date Selection */}
            <div className="bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-full shadow-lg px-1 h-10 flex items-center">
                <div className="flex items-center gap-2 px-3 border-r border-gray-200 dark:border-gray-800 h-full">
                    <span className="text-sm font-medium text-gray-500">Date:</span>
                </div>
                <Select value={selectedDate} onValueChange={onDateChange}>
                    <SelectTrigger className="border-none focus:ring-0 h-full gap-2 bg-transparent w-[140px]">
                        <SelectValue placeholder="Select Date" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="Dec 2025">Dec 2025</SelectItem>
                        <SelectItem value="Nov 2025">Nov 2025</SelectItem>
                        <SelectItem value="Oct 2025">Oct 2025</SelectItem>
                        <SelectItem value="Sep 2025">Sep 2025</SelectItem>
                        <SelectItem value="Aug 2025">Aug 2025</SelectItem>
                        <SelectItem value="Jul 2025">Jul 2025</SelectItem>
                    </SelectContent>
                </Select>
            </div>
        </div>
    )
}
