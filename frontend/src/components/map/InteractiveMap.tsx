"use client";

import { APIProvider, Map, AdvancedMarker, Pin, useMap } from '@vis.gl/react-google-maps';
import { useAppStore } from '@/lib/store';
import { useEffect } from 'react';

interface InteractiveMapProps {
    leads: any[];
    onSelect: (lead: any) => void;
}

function MapController({ leads, selectedProperty }: { leads: any[], selectedProperty: any }) {
    const map = useMap();

    useEffect(() => {
        if (!map) return;

        // 1. Handle Selected Property (Priority)
        if (selectedProperty?.latitude && selectedProperty?.longitude) {
            map.panTo({ lat: selectedProperty.latitude, lng: selectedProperty.longitude });
            map.setZoom(18);
            return;
        }

        // 2. Handle Search Results (Auto-Fit)
        if (leads.length > 0) {
            if (leads.length === 1) {
                const lead = leads[0];
                if (lead.latitude && lead.longitude) {
                    map.panTo({ lat: lead.latitude, lng: lead.longitude });
                    map.setZoom(18);
                }
            } else {
                const bounds = new google.maps.LatLngBounds();
                let hasValidCoords = false;
                leads.forEach(lead => {
                    if (lead.latitude && lead.longitude) {
                        bounds.extend({ lat: lead.latitude, lng: lead.longitude });
                        hasValidCoords = true;
                    }
                });

                if (hasValidCoords) {
                    map.fitBounds(bounds);
                }
            }
        }
    }, [leads, selectedProperty, map]);

    return null;
}

export function InteractiveMap({ leads, onSelect }: InteractiveMapProps) {
    const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
    const { selectedProperty } = useAppStore();

    if (!apiKey) {
        return <div className="flex-1 flex items-center justify-center text-red-500">Missing Google Maps API Key</div>;
    }

    return (
        <div className="flex-1 relative h-full w-full">
            <Map
                defaultCenter={{ lat: 32.2226, lng: -110.9747 }} // Tucson
                defaultZoom={12}
                mapId="DEMO_MAP_ID" // Required for AdvancedMarker
                gestureHandling={'greedy'}
                disableDefaultUI={true}
                className="w-full h-full"
                style={{ width: '100%', height: '100%' }}
            >
                <MapController leads={leads} selectedProperty={selectedProperty} />

                {leads.map((lead) => (
                    lead.latitude && lead.longitude && (
                        <AdvancedMarker
                            key={lead.id}
                            position={{ lat: lead.latitude, lng: lead.longitude }}
                            onClick={() => onSelect(lead)}
                        >
                            <Pin
                                background={lead.score && lead.score > 80 ? '#ef4444' : '#10b981'}
                                borderColor={'#000'}
                                glyphColor={'#fff'}
                            />
                        </AdvancedMarker>
                    )
                ))}
            </Map>

            {/* HUD Elements Overlay */}
            <div className="absolute bottom-8 left-8 p-4 bg-background/80 backdrop-blur border border-border rounded-md pointer-events-none z-10">
                <div className="text-xs font-mono text-muted-foreground">STATUS</div>
                <div className="text-sm font-bold font-mono text-primary">LIVE MAP FEED</div>
            </div>
        </div>
    );
}
