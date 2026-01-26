"use client"

import React, { useEffect, useState, useMemo } from 'react'
import { APIProvider, Map, useMap } from '@vis.gl/react-google-maps'
import { useAppStore } from '@/lib/store'

export type DataLayerType = 'home_value' | 'inventory' | 'days_on_market' | 'price_drops' |
    'home_value_growth_yoy' | 'new_listings' | 'home_sales' | 'price_forecast' |
    'cap_rate' | 'rental_yield' | 'rent_price' | 'overvalued_pct' |
    'population_growth' | 'migration' | 'income'

export type ViewMode = 'national' | 'state' | 'metro' | 'county' | 'zip'

interface MarketMapProps {
    activeLayer: DataLayerType
    viewMode: ViewMode
    tooltipEnabled: boolean
    onRegionClick?: (regionId: string, data: any) => void
}

const TUCSON_CENTER = { lat: 32.2226, lng: -110.9747 }
const USA_CENTER = { lat: 39.8283, lng: -98.5795 }

// Mock GeoJSON Data Generator (Square grids for demo)
const generateMockGeoJson = (mode: ViewMode) => {
    const features = []
    // Adjust grid size based on view mode
    const step = mode === 'zip' ? 0.04 : mode === 'county' ? 0.5 : mode === 'metro' ? 1.0 : 2.0
    const startLat = mode === 'national' ? 25 : 32.15
    const startLng = mode === 'national' ? -125 : -111.05
    const count = mode === 'national' ? 15 : 5

    for (let i = 0; i < count; i++) {
        for (let j = 0; j < count; j++) {
            const lat = startLat + (i * step)
            const lng = startLng + (j * step)
            const value = Math.floor(Math.random() * 500000) + 200000 // Random home value

            features.push({
                type: "Feature",
                properties: {
                    id: `region-${i}-${j}`,
                    name: mode === 'zip' ? `857${i}${j}` : `Region ${i}-${j}`,
                    home_value: value,
                    cap_rate: (Math.random() * 10).toFixed(1),
                    inventory: Math.floor(Math.random() * 50),
                    days_on_market: Math.floor(Math.random() * 90),
                    price_drops: Math.floor(Math.random() * 20)
                },
                geometry: {
                    type: "Polygon",
                    coordinates: [[
                        [lng, lat],
                        [lng + (step * 0.9), lat],
                        [lng + (step * 0.9), lat + (step * 0.9)],
                        [lng, lat + (step * 0.9)],
                        [lng, lat]
                    ]]
                }
            })
        }
    }
    return { type: "FeatureCollection", features }
}

const MapLayerController = ({ activeLayer, viewMode, tooltipEnabled, onRegionClick }: MarketMapProps) => {
    const map = useMap()
    const [geoJsonData, setGeoJsonData] = useState(generateMockGeoJson(viewMode))
    const [hoveredFeature, setHoveredFeature] = useState<{ x: number, y: number, properties: any } | null>(null)

    // Update data when view mode changes
    useEffect(() => {
        setGeoJsonData(generateMockGeoJson(viewMode))
    }, [viewMode])

    // Update Map Zoom/Center based on View Mode
    useEffect(() => {
        if (!map) return
        if (viewMode === 'national') {
            map.setCenter(USA_CENTER)
            map.setZoom(4)
        } else if (viewMode === 'state') {
            map.setCenter(TUCSON_CENTER) // Mock: Arizona
            map.setZoom(7)
        } else if (viewMode === 'metro') {
            map.setCenter(TUCSON_CENTER)
            map.setZoom(8)
        } else if (viewMode === 'county') {
            map.setCenter(TUCSON_CENTER)
            map.setZoom(9)
        } else {
            map.setCenter(TUCSON_CENTER)
            map.setZoom(11)
        }
    }, [map, viewMode])

    useEffect(() => {
        if (!map) return

        // Clear existing data
        map.data.forEach(feature => {
            map.data.remove(feature)
        })

        // Add new data
        map.data.addGeoJson(geoJsonData)

        // Style function based on active layer
        map.data.setStyle((feature) => {
            const value = feature.getProperty('home_value') as number // Simplified: using home_value for all for demo
            let color = '#cccccc'

            // Simple heatmap logic
            if (value > 600000) color = '#1a9850'
            else if (value > 500000) color = '#91cf60'
            else if (value > 400000) color = '#d9ef8b'
            else if (value > 300000) color = '#fee08b'
            else if (value > 200000) color = '#fc8d59'
            else color = '#d73027'

            return {
                fillColor: color,
                fillOpacity: 0.6,
                strokeWeight: 1,
                strokeColor: '#ffffff',
                clickable: true
            }
        })

        // Event Listeners
        const clickListener = map.data.addListener('click', (event: any) => {
            const id = event.feature.getProperty('id')
            const data = {
                home_value: event.feature.getProperty('home_value'),
                cap_rate: event.feature.getProperty('cap_rate'),
                inventory: event.feature.getProperty('inventory'),
            }
            onRegionClick?.(id, data)
        })

        const mouseOverListener = map.data.addListener('mouseover', (event: any) => {
            map.data.overrideStyle(event.feature, { fillOpacity: 0.8, strokeWeight: 2 })

            if (tooltipEnabled) {
                // Calculate position (simplified)
                // In a real app, we'd project lat/lng to pixels
                // For now, we'll rely on the mouse event if available, or just show it fixed
                // Google Maps JS API event doesn't give pixel coordinates easily without OverlayView
                // So we'll skip the floating tooltip *positioning* logic here and just set state
                // A real implementation would use a custom OverlayView for the tooltip
            }
        })

        const mouseOutListener = map.data.addListener('mouseout', (event: any) => {
            map.data.revertStyle()
            setHoveredFeature(null)
        })

        return () => {
            google.maps.event.removeListener(clickListener)
            google.maps.event.removeListener(mouseOverListener)
            google.maps.event.removeListener(mouseOutListener)
        }

    }, [map, activeLayer, geoJsonData, onRegionClick, tooltipEnabled])

    return null
}

export function MarketMap({ activeLayer, viewMode, tooltipEnabled, onRegionClick }: MarketMapProps) {
    const { googleMapsApiKey } = useAppStore();

    if (!googleMapsApiKey) return <div className="h-full w-full bg-gray-900 flex items-center justify-center text-gray-500">Loading Map...</div>;

    return (
        <APIProvider apiKey={googleMapsApiKey}>
            <div className="h-full w-full bg-gray-900 relative">
                <Map
                    defaultCenter={TUCSON_CENTER}
                    defaultZoom={11}
                    mapId="MARKET_MAP_ID"
                    className="h-full w-full"
                    disableDefaultUI={true}
                    gestureHandling={'greedy'}
                    colorScheme="DARK"
                >
                    <MapLayerController
                        activeLayer={activeLayer}
                        viewMode={viewMode}
                        tooltipEnabled={tooltipEnabled}
                        onRegionClick={onRegionClick}
                    />
                </Map>

                {/* Simple Tooltip Overlay (Placeholder for real OverlayView) */}
                {tooltipEnabled && (
                    <div className="absolute top-4 right-4 bg-black/80 text-white p-2 rounded text-xs pointer-events-none z-10">
                        Tooltip Active (Hover regions)
                    </div>
                )}
            </div>
        </APIProvider>
    )
}
