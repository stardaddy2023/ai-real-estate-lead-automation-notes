"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import Link from "next/link"

interface DealMetricsProps {
    leadId: string
}

export function DealMetrics({ leadId }: DealMetricsProps) {
    const [arv, setArv] = useState<string>("0")
    const [repairs, setRepairs] = useState<string>("0")

    const arvValue = parseFloat(arv) || 0
    const repairsValue = parseFloat(repairs) || 0
    const maxOffer = (arvValue * 0.7) - repairsValue

    return (
        <Card>
            <CardHeader>
                <CardTitle>Offer Calculator</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <Label htmlFor="arv">After Repair Value (ARV)</Label>
                        <Input
                            id="arv"
                            type="number"
                            value={arv}
                            onChange={(e) => setArv(e.target.value)}
                            placeholder="e.g. 100000"
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="repairs">Estimated Repairs</Label>
                        <Input
                            id="repairs"
                            type="number"
                            value={repairs}
                            onChange={(e) => setRepairs(e.target.value)}
                            placeholder="e.g. 10000"
                        />
                    </div>
                </div>

                <div className="pt-4 border-t">
                    <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-muted-foreground">Max Allowable Offer (MAO)</span>
                        <span className="text-2xl font-bold text-green-600">
                            ${maxOffer.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1 text-right">
                        (ARV * 70%) - Repairs
                    </p>
                </div>

                <Button className="w-full" asChild>
                    <Link href={`/leads/${leadId}/offer`}>Generate Offer</Link>
                </Button>
            </CardContent>
        </Card>
    )
}
