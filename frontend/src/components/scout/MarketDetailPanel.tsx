"use client"

import React, { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { X, Maximize2, Download, Table as TableIcon, TrendingUp } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'

interface MarketDetailPanelProps {
    regionId: string
    data: any
    onClose: () => void
}

// Mock Historical Data
const generateHistory = () => {
    const data = []
    for (let i = 2005; i <= 2025; i++) {
        data.push({
            year: i,
            value: Math.floor(Math.random() * 300000) + 200000 + (i - 2005) * 20000
        })
    }
    return data
}

export function MarketDetailPanel({ regionId, data, onClose }: MarketDetailPanelProps) {
    const [history] = useState(generateHistory())
    const [view, setView] = useState<'chart' | 'table'>('chart')

    return (
        <div className="absolute top-20 right-4 bottom-24 w-[500px] bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-xl shadow-2xl flex flex-col z-20 overflow-hidden">

            {/* Header */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-800 flex justify-between items-start bg-gray-50 dark:bg-gray-900/50">
                <div>
                    <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
                        <span>Zip: {regionId}</span>
                        <span>•</span>
                        <span>Pima County, AZ</span>
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                        ${data.home_value.toLocaleString()}
                    </h2>
                    <div className="flex items-center gap-2 text-sm mt-1">
                        <span className="text-gray-500">Home Value</span>
                        <span className="text-green-500 font-medium flex items-center bg-green-100 dark:bg-green-900/30 px-1.5 py-0.5 rounded text-xs">
                            <TrendingUp className="w-3 h-3 mr-1" />
                            +5.2% YoY
                        </span>
                    </div>
                </div>
                <div className="flex gap-2">
                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}>
                        <X className="w-4 h-4" />
                    </Button>
                </div>
            </div>

            {/* Controls */}
            <div className="p-3 border-b border-gray-200 dark:border-gray-800 flex justify-between items-center">
                <div className="flex bg-gray-100 dark:bg-gray-900 rounded-lg p-1">
                    <button
                        onClick={() => setView('chart')}
                        className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${view === 'chart' ? 'bg-white dark:bg-gray-800 shadow text-gray-900 dark:text-white' : 'text-gray-500 hover:text-gray-900 dark:hover:text-gray-300'}`}
                    >
                        Chart
                    </button>
                    <button
                        onClick={() => setView('table')}
                        className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${view === 'table' ? 'bg-white dark:bg-gray-800 shadow text-gray-900 dark:text-white' : 'text-gray-500 hover:text-gray-900 dark:hover:text-gray-300'}`}
                    >
                        Table
                    </button>
                </div>
                <Button variant="outline" size="sm" className="h-8 text-xs gap-1">
                    <Download className="w-3 h-3" />
                    Export
                </Button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
                {view === 'chart' ? (
                    <div className="space-y-6">
                        {/* Gauge / Score */}
                        <div className="bg-gray-50 dark:bg-gray-900/30 rounded-lg p-4 border border-gray-100 dark:border-gray-800">
                            <h3 className="text-sm font-semibold mb-4 text-center">Market Forecast Score</h3>
                            <div className="relative h-32 flex items-end justify-center pb-2">
                                <div className="absolute top-0 w-48 h-24 bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 rounded-t-full opacity-20"></div>
                                <div className="absolute top-0 w-48 h-24 border-[12px] border-gray-200 dark:border-gray-800 rounded-t-full border-b-0"></div>
                                {/* Needle (Mock) */}
                                <div className="absolute bottom-0 w-1 h-24 bg-gray-800 dark:bg-white origin-bottom transform -rotate-45 transition-transform duration-1000"></div>
                                <div className="absolute bottom-0 w-4 h-4 bg-gray-800 dark:bg-white rounded-full"></div>
                            </div>
                            <div className="text-center mt-2">
                                <span className="text-2xl font-bold text-yellow-500">6.5</span>
                                <span className="text-xs text-gray-500 block">Neutral / Hold</span>
                            </div>
                        </div>

                        {/* Line Chart */}
                        <div className="h-64 w-full">
                            <h3 className="text-sm font-semibold mb-4">Historical Trend</h3>
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={history}>
                                    <defs>
                                        <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#374151" opacity={0.2} />
                                    <XAxis
                                        dataKey="year"
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fontSize: 10, fill: '#6b7280' }}
                                    />
                                    <YAxis
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fontSize: 10, fill: '#6b7280' }}
                                        tickFormatter={(value) => `$${value / 1000}k`}
                                    />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px', color: '#fff' }}
                                        itemStyle={{ color: '#fff' }}
                                        formatter={(value: number) => [`$${value.toLocaleString()}`, 'Value']}
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="value"
                                        stroke="#22c55e"
                                        strokeWidth={2}
                                        fillOpacity={1}
                                        fill="url(#colorValue)"
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Stats Grid */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-3 bg-gray-50 dark:bg-gray-900/30 rounded border border-gray-100 dark:border-gray-800">
                                <div className="text-xs text-gray-500">Inventory</div>
                                <div className="text-lg font-bold">{data.inventory}</div>
                            </div>
                            <div className="p-3 bg-gray-50 dark:bg-gray-900/30 rounded border border-gray-100 dark:border-gray-800">
                                <div className="text-xs text-gray-500">Days on Market</div>
                                <div className="text-lg font-bold">{data.days_on_market}</div>
                            </div>
                            <div className="p-3 bg-gray-50 dark:bg-gray-900/30 rounded border border-gray-100 dark:border-gray-800">
                                <div className="text-xs text-gray-500">Price Drops</div>
                                <div className="text-lg font-bold">{data.price_drops}%</div>
                            </div>
                            <div className="p-3 bg-gray-50 dark:bg-gray-900/30 rounded border border-gray-100 dark:border-gray-800">
                                <div className="text-xs text-gray-500">Rent Price</div>
                                <div className="text-lg font-bold">$2,150</div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-4">
                        <table className="w-full text-sm text-left">
                            <thead className="text-xs text-gray-500 uppercase bg-gray-50 dark:bg-gray-900/50">
                                <tr>
                                    <th className="px-4 py-3 rounded-l-lg">Year</th>
                                    <th className="px-4 py-3">Value</th>
                                    <th className="px-4 py-3 rounded-r-lg">Change</th>
                                </tr>
                            </thead>
                            <tbody>
                                {history.map((row, i) => (
                                    <tr key={row.year} className="border-b border-gray-100 dark:border-gray-800">
                                        <td className="px-4 py-3 font-medium">{row.year}</td>
                                        <td className="px-4 py-3">${row.value.toLocaleString()}</td>
                                        <td className={`px-4 py-3 ${i > 0 && row.value > history[i - 1].value ? 'text-green-500' : 'text-red-500'}`}>
                                            {i > 0 ? ((row.value - history[i - 1].value) / history[i - 1].value * 100).toFixed(1) + '%' : '-'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    )
}
