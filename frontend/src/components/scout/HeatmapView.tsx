"use client"

import { useEffect, useState } from "react"
import dynamic from "next/dynamic"
import "leaflet/dist/leaflet.css"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

// Dynamically import MapContainer and other Leaflet components to avoid SSR issues
const MapContainer = dynamic(
    () => import("react-leaflet").then((mod) => mod.MapContainer),
    { ssr: false }
)
const TileLayer = dynamic(
    () => import("react-leaflet").then((mod) => mod.TileLayer),
    { ssr: false }
)
const CircleMarker = dynamic(
    () => import("react-leaflet").then((mod) => mod.CircleMarker),
    { ssr: false }
)
const Popup = dynamic(
    () => import("react-leaflet").then((mod) => mod.Popup),
    { ssr: false }
)

interface HeatmapPoint {
    lat: number
    lng: number
    weight: number
    zip_code: string
}

export function HeatmapView() {
    const [data, setData] = useState<HeatmapPoint[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        async function fetchData() {
            try {
                const res = await fetch("http://127.0.0.1:8000/api/v1/scout/heatmap")
                if (res.ok) {
                    const points = await res.json()
                    setData(points)
                }
            } catch (error) {
                console.error("Failed to fetch heatmap data", error)
            } finally {
                setLoading(false)
            }
        }
        fetchData()
    }, [])

    return (
        <Card className="h-[600px] flex flex-col">
            <CardHeader>
                <CardTitle>Market Heatmap (Distress Score)</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 p-0 relative min-h-[500px] overflow-hidden rounded-b-lg">
                <MapContainer
                    center={[32.2217, -110.9719]}
                    zoom={11}
                    style={{ height: "100%", width: "100%" }}
                >
                    <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    {data.map((point, idx) => (
                        <CircleMarker
                            key={idx}
                            center={[point.lat, point.lng]}
                            radius={10}
                            pathOptions={{
                                color: point.weight > 0.7 ? 'red' : point.weight > 0.4 ? 'orange' : 'green',
                                fillOpacity: 0.6,
                                weight: 1
                            }}
                        >
                            <Popup>
                                <div className="text-sm">
                                    <strong>Zip: {point.zip_code}</strong><br />
                                    Distress Score: {(point.weight * 100).toFixed(0)}
                                </div>
                            </Popup>
                        </CircleMarker>
                    ))}
                </MapContainer>
            </CardContent>
        </Card>
    )
}
