"use client"

import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { Lead } from '@/types'
import { Icon } from 'leaflet'

// Fix for default marker icon in Next.js
const defaultIcon = new Icon({
    iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
})

interface LeadMapProps {
    leads: Lead[]
}

export function LeadMap({ leads }: LeadMapProps) {
    // Default center (Tucson)
    const center: [number, number] = [32.2226, -110.9747]

    return (
        <div className="h-[600px] w-full rounded-lg border overflow-hidden">
            <MapContainer
                center={center}
                zoom={11}
                style={{ height: '100%', width: '100%' }}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                {leads.map((lead) => {
                    // Skip if no coordinates (mocking coords if missing for demo)
                    const leadAny = lead as any;
                    const lat = leadAny.latitude || (32.2226 + (Math.random() - 0.5) * 0.1)
                    const lng = leadAny.longitude || (-110.9747 + (Math.random() - 0.5) * 0.1)

                    return (
                        <Marker
                            key={lead.id}
                            position={[lat, lng]}
                            icon={defaultIcon}
                        >
                            <Popup>
                                <div className="p-2">
                                    <h3 className="font-bold">{lead.address_street}</h3>
                                    <p className="text-sm text-gray-600">Status: {lead.status}</p>
                                    <p className="text-sm font-semibold mt-1">
                                        Distress: {lead.distress_score}
                                    </p>
                                </div>
                            </Popup>
                        </Marker>
                    )
                })}
            </MapContainer>
        </div>
    )
}
