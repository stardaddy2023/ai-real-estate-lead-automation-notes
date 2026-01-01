"use client"

import React, { useEffect, useState, useCallback } from 'react'
import { APIProvider, Map, AdvancedMarker, Pin, useMap } from '@vis.gl/react-google-maps'
import { ScoutResult } from './LeadScout'

interface GoogleScoutMapProps {
    leads: ScoutResult[]
    highlightedLeadId?: string | null
    panToLeadId?: string | null
    onMarkerClick: (lead: ScoutResult) => void
    onMapClick?: () => void
}

const MapController = ({ leads, panToLeadId }: { leads: ScoutResult[], panToLeadId?: string | null }) => {
    const map = useMap()

    useEffect(() => {
        if (!map || leads.length === 0) return

        // If only one result, pan and zoom to it
        if (leads.length === 1) {
            const lead = leads[0]
            if (lead.latitude && lead.longitude) {
                map.panTo({ lat: lead.latitude, lng: lead.longitude })
                map.setZoom(18)
            }
            return
        }

        // Multiple results: Fit bounds
        const bounds = new google.maps.LatLngBounds()
        let hasValidCoords = false
        leads.forEach(lead => {
            if (lead.latitude && lead.longitude) {
                bounds.extend({ lat: lead.latitude, lng: lead.longitude })
                hasValidCoords = true
            }
        })

        if (hasValidCoords) {
            map.fitBounds(bounds)
            // Optional: Add padding if needed, though default usually works
        }
    }, [map, leads])

    useEffect(() => {
        if (!map || !panToLeadId) return

        const lead = leads.find(l => (l.id === panToLeadId || l.parcel_id === panToLeadId))
        if (lead && lead.latitude && lead.longitude) {
            map.panTo({ lat: lead.latitude, lng: lead.longitude })
            // Don't zoom in on hover, just pan.
        }
    }, [map, panToLeadId, leads])

    return null
}

export function GoogleScoutMap({ leads, highlightedLeadId, panToLeadId, onMarkerClick, onMapClick }: GoogleScoutMapProps) {
    const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || ""

    // Default center (Tucson)
    const defaultCenter = { lat: 32.2226, lng: -110.9747 }

    console.log("GoogleScoutMap received leads:", leads)

    return (
        <APIProvider apiKey={apiKey}>
            <div className="h-full w-full rounded-md overflow-hidden">
                <Map
                    defaultCenter={defaultCenter}
                    defaultZoom={12}
                    mapId="DEMO_MAP_ID" // Required for AdvancedMarker
                    className="h-full w-full"
                    disableDefaultUI={false}
                    onClick={() => onMapClick && onMapClick()}
                >
                    <MapController leads={leads} panToLeadId={panToLeadId} />

                    {leads.map((lead, index) => (
                        lead.latitude && lead.longitude ? (
                            <AdvancedMarker
                                key={lead.id || `map-marker-${index}`}
                                position={{ lat: Number(lead.latitude), lng: Number(lead.longitude) }}
                                onClick={() => onMarkerClick(lead)}
                                title={lead.address}
                            >
                                <Pin
                                    background={highlightedLeadId === lead.id ? "#22c55e" : "#ef4444"}
                                    borderColor={"#000"}
                                    glyphColor={"#fff"}
                                    scale={highlightedLeadId === lead.id ? 1.2 : 1.0}
                                />
                            </AdvancedMarker>
                        ) : null
                    ))}
                </Map>
            </div>
        </APIProvider>
    )
}
