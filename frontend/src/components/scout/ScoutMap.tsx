"use client"

import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { Icon } from 'leaflet'
import { useEffect } from 'react'

// Default Icon
const defaultIcon = new Icon({
    iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
})

// Highlight Icon (Red)
const highlightIcon = new Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
})

interface ScoutResult {
    id?: string
    parcel_id?: string
    address?: string
    latitude?: number
    longitude?: number
    owner_name?: string
    distress_signals?: string[]
}

interface ScoutMapProps {
    leads: ScoutResult[]
    hoveredLeadId?: string | null
    onMarkerClick?: (lead: ScoutResult) => void
}

// Component to update map center/zoom when leads change
function MapUpdater({ leads }: { leads: ScoutResult[] }) {
    const map = useMap()

    useEffect(() => {
        if (leads.length > 0) {
            // Calculate bounds
            const lats = leads.map(l => l.latitude).filter(l => l !== undefined) as number[]
            const lngs = leads.map(l => l.longitude).filter(l => l !== undefined) as number[]

            if (lats.length > 0 && lngs.length > 0) {
                const minLat = Math.min(...lats)
                const maxLat = Math.max(...lats)
                const minLng = Math.min(...lngs)
                const maxLng = Math.max(...lngs)

                map.fitBounds([
                    [minLat, minLng],
                    [maxLat, maxLng]
                ], { padding: [50, 50] })
            }
        }
    }, [leads, map])

    return null
}

export function ScoutMap({ leads, hoveredLeadId, onMarkerClick }: ScoutMapProps) {
    // Default center (Tucson)
    const center: [number, number] = [32.2226, -110.9747]

    return (
        <div className="h-full w-full relative z-0">
            <MapContainer
                center={center}
                zoom={11}
                style={{ height: '100%', width: '100%' }}
                scrollWheelZoom={true}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <MapUpdater leads={leads} />

                {leads.map((lead, idx) => {
                    // Fallback ID if missing
                    const leadId = lead.id || lead.parcel_id || `idx-${idx}`

                    // Skip if no coordinates
                    if (!lead.latitude || !lead.longitude) return null

                    const isHovered = hoveredLeadId === leadId

                    return (
                        <Marker
                            key={leadId}
                            position={[lead.latitude, lead.longitude]}
                            icon={isHovered ? highlightIcon : defaultIcon}
                            zIndexOffset={isHovered ? 1000 : 0}
                            eventHandlers={{
                                click: () => onMarkerClick?.(lead)
                            }}
                        >
                            <Popup>
                                <div className="p-2 min-w-[200px]">
                                    <h3 className="font-bold text-sm">{lead.address}</h3>
                                    <p className="text-xs text-gray-600 mb-1">{lead.owner_name}</p>
                                    <div className="flex flex-wrap gap-1">
                                        {lead.distress_signals?.map((s, i) => (
                                            <span key={i} className="text-[10px] bg-red-100 text-red-800 px-1 rounded">
                                                {s}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            </Popup>
                        </Marker>
                    )
                })}
            </MapContainer>
        </div>
    )
}
