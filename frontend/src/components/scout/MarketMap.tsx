"use client"

import React, { useEffect, useState, useMemo } from 'react'
import { APIProvider, Map, useMap } from '@vis.gl/react-google-maps'
import { useAppStore } from '@/lib/store'

export type DataLayerType = 'home_value' | 'inventory' | 'days_on_market' | 'price_drops'

interface MarketMapProps {
    activeLayer: DataLayerType
    onRegionClick?: (regionId: string, data: any) => void
}

const TUCSON_CENTER = { lat: 32.2226, lng: -110.9747 }

// Mock GeoJSON Data Generator (Square grids for demo)
const generateMockGeoJson = () => {
    const features = []
    const startLat = 32.15
    const startLng = -111.05

    for (let i = 0; i < 5; i++) {
        for (let j = 0; j < 5; j++) {
            const lat = startLat + (i * 0.04)
            const lng = startLng + (j * 0.04)
            const value = Math.floor(Math.random() * 500000) + 200000 // Random home value

            features.push({
                type: "Feature",
                properties: {
                    zip: `857${i}${j}`,
                    home_value: value,
                    inventory: Math.floor(Math.random() * 50),
                    days_on_market: Math.floor(Math.random() * 90),
                    price_drops: Math.floor(Math.random() * 20)
                },
                geometry: {
                    type: "Polygon",
                    coordinates: [[
                        [lng, lat],
                        [lng + 0.035, lat],
                        [lng + 0.035, lat + 0.035],
                        [lng, lat + 0.035],
                        [lng, lat]
                    ]]
                }
            })
        }
    }
    return { type: "FeatureCollection", features }
}

const MapLayerController = ({ activeLayer, onRegionClick }: MarketMapProps) => {
    const map = useMap()
    const [geoJsonData] = useState(generateMockGeoJson())

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
            const value = feature.getProperty(activeLayer) as number
            let color = '#cccccc'

            if (activeLayer === 'home_value') {
                if (value > 600000) color = '#1a9850'
                else if (value > 500000) color = '#91cf60'
                else if (value > 400000) color = '#d9ef8b'
                else if (value > 300000) color = '#fee08b'
                else if (value > 200000) color = '#fc8d59'
                else color = '#d73027'
            } else if (activeLayer === 'inventory') {
                // High inventory = Blue, Low = Red
                if (value > 40) color = '#4575b4'
                else if (value > 30) color = '#91bfdb'
                else if (value > 20) color = '#e0f3f8'
                else if (value > 10) color = '#fee090'
                else color = '#d73027'
            }

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
            const zip = event.feature.getProperty('zip')
            const data = {
                home_value: event.feature.getProperty('home_value'),
                inventory: event.feature.getProperty('inventory'),
                days_on_market: event.feature.getProperty('days_on_market'),
                price_drops: event.feature.getProperty('price_drops')
            }
            onRegionClick?.(zip, data)
        })

        const mouseOverListener = map.data.addListener('mouseover', (event: any) => {
            map.data.overrideStyle(event.feature, { fillOpacity: 0.8, strokeWeight: 2 })
        })

        const mouseOutListener = map.data.addListener('mouseout', (event: any) => {
            map.data.revertStyle()
        })

        return () => {
            google.maps.event.removeListener(clickListener)
            google.maps.event.removeListener(mouseOverListener)
            google.maps.event.removeListener(mouseOutListener)
        }

    }, [map, activeLayer, geoJsonData, onRegionClick])

    return null
}

export function MarketMap({ activeLayer, onRegionClick }: MarketMapProps) {
    const { googleMapsApiKey } = useAppStore();

    if (!googleMapsApiKey) return <div className="h-full w-full bg-gray-900 flex items-center justify-center text-gray-500">Loading Map...</div>;

    return (
        <APIProvider apiKey={googleMapsApiKey}>
            <div className="h-full w-full bg-gray-900">
                <Map
                    defaultCenter={TUCSON_CENTER}
                    defaultZoom={11}
                    mapId="MARKET_MAP_ID"
                    className="h-full w-full"
                    disableDefaultUI={true}
                    gestureHandling={'greedy'}
                    colorScheme="DARK"
                >
                    <MapLayerController activeLayer={activeLayer} onRegionClick={onRegionClick} />
                </Map>
            </div>
        </APIProvider>
    )
}
