"use client"

import React, { useEffect, useState, useCallback, useRef } from 'react'
import { APIProvider, Map, AdvancedMarker, Pin, useMap, useMapsLibrary } from '@vis.gl/react-google-maps'
import { useAppStore } from '@/lib/store'
import { Button } from '@/components/ui/button'
import { Pencil, X, Search } from 'lucide-react'
import { ScoutResult } from '@/lib/store'

interface GoogleScoutMapProps {
    leads: ScoutResult[]
    highlightedLeadId?: string | null
    panToLeadId?: string | null
    onMarkerClick: (lead: ScoutResult) => void
    onMapClick?: () => void
    onMapSelection?: (bounds: { north: number, south: number, east: number, west: number } | null) => void
    onSearchArea?: (bounds: { north: number, south: number, east: number, west: number }) => void
    selectedBounds?: { north: number, south: number, east: number, west: number } | null
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

const DrawingManager = ({ onSelection, isDrawing, setIsDrawing, initialBounds }: {
    onSelection: (bounds: { north: number, south: number, east: number, west: number }) => void,
    isDrawing: boolean,
    setIsDrawing: (isDrawing: boolean) => void,
    initialBounds?: { north: number, south: number, east: number, west: number } | null
}) => {
    const map = useMap()
    const drawingLib = useMapsLibrary('drawing')
    const [drawingManager, setDrawingManager] = useState<google.maps.drawing.DrawingManager | null>(null)
    const rectangleRef = useRef<google.maps.Rectangle | null>(null)

    // Effect to restore bounds on mount or update, OR clear when null
    useEffect(() => {
        if (!map) return

        // If initialBounds is null, clear the existing rectangle
        if (!initialBounds && rectangleRef.current) {
            rectangleRef.current.setMap(null)
            rectangleRef.current = null
            return
        }

        // If initialBounds exists and we don't have a rectangle, create one
        if (initialBounds && !rectangleRef.current) {
            const rectangle = new google.maps.Rectangle({
                bounds: initialBounds,
                fillColor: '#22c55e',
                fillOpacity: 0.2,
                strokeWeight: 2,
                strokeColor: '#22c55e',
                editable: true,
                draggable: true,
                map: map
            })

            rectangleRef.current = rectangle

            // Add listeners to existing rectangle
            google.maps.event.addListener(rectangle, 'bounds_changed', () => {
                const newBounds = rectangle.getBounds()
                if (newBounds) {
                    onSelection(newBounds.toJSON())
                }
            })
        }
    }, [map, initialBounds]) // Runs when map or initialBounds change

    useEffect(() => {
        if (!map || !drawingLib) return

        const manager = new drawingLib.DrawingManager({
            drawingMode: null,
            drawingControl: false,
            rectangleOptions: {
                fillColor: '#22c55e',
                fillOpacity: 0.2,
                strokeWeight: 2,
                strokeColor: '#22c55e',
                editable: true,
                draggable: true
            }
        })

        manager.setMap(map)
        setDrawingManager(manager)

        return () => {
            manager.setMap(null)
        }
    }, [map, drawingLib])

    useEffect(() => {
        if (!drawingManager) return

        if (isDrawing) {
            drawingManager.setDrawingMode(google.maps.drawing.OverlayType.RECTANGLE)
            // Clear existing rectangle if any
            if (rectangleRef.current) {
                rectangleRef.current.setMap(null)
                rectangleRef.current = null
            }
        } else {
            drawingManager.setDrawingMode(null)
        }
    }, [isDrawing, drawingManager])

    useEffect(() => {
        if (!drawingManager) return

        const listener = google.maps.event.addListener(drawingManager, 'overlaycomplete', (event: any) => {
            if (event.type === 'rectangle') {
                const rectangle = event.overlay as google.maps.Rectangle
                rectangleRef.current = rectangle

                const bounds = rectangle.getBounds()
                if (bounds) {
                    const json = bounds.toJSON()
                    onSelection(json)
                }

                // Stop drawing mode but keep rectangle
                setIsDrawing(false)

                // Add listeners for edit/drag
                google.maps.event.addListener(rectangle, 'bounds_changed', () => {
                    const newBounds = rectangle.getBounds()
                    if (newBounds) {
                        onSelection(newBounds.toJSON())
                    }
                })
            }
        })

        return () => {
            google.maps.event.removeListener(listener)
        }
    }, [drawingManager, onSelection, setIsDrawing])

    return null
}

export function GoogleScoutMap({ leads, highlightedLeadId, panToLeadId, onMarkerClick, onMapClick, onMapSelection, onSearchArea, selectedBounds }: GoogleScoutMapProps) {
    const { googleMapsApiKey: apiKey } = useAppStore()
    const isLoading = !apiKey
    const [isDrawing, setIsDrawing] = useState(false)

    if (isLoading) {
        return <div className="h-full w-full flex items-center justify-center bg-muted/20">Loading Map...</div>
    }

    // Clear selection handler
    const handleClearSelection = () => {
        setIsDrawing(false)
        if (onMapSelection) onMapSelection(null)
        // Note: Clearing the visual rectangle is handled by DrawingManager re-mount or state logic, 
        // but since we don't expose a clear method, we might need a ref or just rely on new search clearing it.
        // For now, let's just trigger the callback.
    }

    // Default center (Tucson)
    const defaultCenter = { lat: 32.2226, lng: -110.9747 }

    console.log("GoogleScoutMap received leads:", leads)

    const LIBRARIES: ("places" | "geometry" | "drawing" | "visualization")[] = ['places', 'geometry', 'drawing'];

    return (
        <APIProvider apiKey={apiKey} libraries={LIBRARIES}>
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

                    {onMapSelection && (
                        <DrawingManager
                            onSelection={onMapSelection}
                            isDrawing={isDrawing}
                            setIsDrawing={setIsDrawing}
                            initialBounds={selectedBounds}
                        />
                    )}

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

                {/* Drawing Tools Overlay */}
                {onMapSelection && (
                    <div className="absolute bottom-8 left-4 z-10 flex flex-col gap-2">
                        <Button
                            variant={isDrawing ? "destructive" : "secondary"}
                            size="sm"
                            onClick={() => setIsDrawing(!isDrawing)}
                            className="shadow-md"
                        >
                            {isDrawing ? <X className="w-4 h-4 mr-2" /> : <Pencil className="w-4 h-4 mr-2" />}
                            {isDrawing ? "Cancel" : "Draw Area"}
                        </Button>

                        {/* Search Area Button - Only visible when bounds exist and not drawing */}
                        {selectedBounds && !isDrawing && onSearchArea && (
                            <>
                                <Button
                                    variant="default"
                                    size="sm"
                                    onClick={() => onSearchArea(selectedBounds)}
                                    className="shadow-md bg-green-600 hover:bg-green-700 text-white animate-in fade-in slide-in-from-left-2"
                                >
                                    <Search className="w-4 h-4 mr-2" />
                                    Search Area
                                </Button>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={handleClearSelection}
                                    className="shadow-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700"
                                >
                                    <X className="w-4 h-4 mr-2" />
                                    Clear Selection
                                </Button>
                            </>
                        )}
                    </div>
                )}
            </div>
        </APIProvider>
    )
}
