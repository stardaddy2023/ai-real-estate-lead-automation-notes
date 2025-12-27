"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { CheckCircle2 } from "lucide-react"
import { useState } from "react"

interface BuyerCardProps {
    name: string
    score: number
    criteria: string[]
}

export function BuyerCard({ name, score, criteria }: BuyerCardProps) {
    const [sent, setSent] = useState(false)

    const handleSend = () => {
        setSent(true)
        console.log(`Deal sent to ${name}`)
    }

    return (
        <Card>
            <CardHeader className="pb-2">
                <div className="flex justify-between items-center">
                    <CardTitle className="text-base font-bold">{name}</CardTitle>
                    <Badge variant={score > 80 ? "default" : "secondary"}>
                        {score}% Match
                    </Badge>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="flex flex-wrap gap-1">
                    {criteria.map((c) => (
                        <span key={c} className="text-xs bg-muted px-2 py-1 rounded-md">
                            {c}
                        </span>
                    ))}
                </div>

                <Button
                    className="w-full"
                    size="sm"
                    onClick={handleSend}
                    disabled={sent}
                    variant={sent ? "outline" : "default"}
                >
                    {sent ? (
                        <>
                            <CheckCircle2 className="mr-2 h-4 w-4 text-green-600" />
                            Sent
                        </>
                    ) : (
                        "Send Deal"
                    )}
                </Button>
            </CardContent>
        </Card>
    )
}
