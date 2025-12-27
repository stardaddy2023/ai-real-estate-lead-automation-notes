"use client"

import { useState } from "react"
import { CalendarIcon, Loader2 } from "lucide-react"
import { format } from "date-fns"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { cn } from "@/lib/utils"
import { ContractPreview } from "./contract-preview"
import { Lead } from "@/types"

interface OfferFormProps {
    lead: Lead
}

export function OfferForm({ lead }: OfferFormProps) {
    const [amount, setAmount] = useState("")
    const [earnestMoney, setEarnestMoney] = useState("1000")
    const [date, setDate] = useState<Date>()
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [isSuccess, setIsSuccess] = useState(false)

    const handleSubmit = async () => {
        setIsSubmitting(true)
        // Simulate API call
        await new Promise((resolve) => setTimeout(resolve, 1500))

        console.log("Offer sent:", {
            leadId: lead.id,
            amount,
            earnestMoney,
            closingDate: date,
        })

        setIsSubmitting(false)
        setIsSuccess(true)
    }

    if (isSuccess) {
        return (
            <Card className="w-full max-w-2xl mx-auto border-green-500/50 bg-green-500/10">
                <CardContent className="pt-6 text-center space-y-4">
                    <div className="text-2xl font-bold text-green-600">Offer Sent Successfully!</div>
                    <p className="text-muted-foreground">The contract has been generated and queued for delivery.</p>
                    <Button variant="outline" onClick={() => setIsSuccess(false)}>Send Another</Button>
                </CardContent>
            </Card>
        )
    }

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
                <CardHeader>
                    <CardTitle>Configure Offer</CardTitle>
                    <CardDescription>Enter the terms for {lead.address_street}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="amount">Offer Amount ($)</Label>
                        <Input
                            id="amount"
                            type="number"
                            placeholder="e.g. 150000"
                            value={amount}
                            onChange={(e) => setAmount(e.target.value)}
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="earnest">Earnest Money ($)</Label>
                        <Input
                            id="earnest"
                            type="number"
                            placeholder="e.g. 1000"
                            value={earnestMoney}
                            onChange={(e) => setEarnestMoney(e.target.value)}
                        />
                    </div>

                    <div className="space-y-2">
                        <Label>Closing Date</Label>
                        <Popover>
                            <PopoverTrigger asChild>
                                <Button
                                    variant={"outline"}
                                    className={cn(
                                        "w-full justify-start text-left font-normal",
                                        !date && "text-muted-foreground"
                                    )}
                                >
                                    <CalendarIcon className="mr-2 h-4 w-4" />
                                    {date ? format(date, "PPP") : <span>Pick a date</span>}
                                </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-auto p-0">
                                <Calendar
                                    mode="single"
                                    selected={date}
                                    onSelect={setDate}
                                    initialFocus
                                />
                            </PopoverContent>
                        </Popover>
                    </div>
                </CardContent>
                <CardFooter>
                    <Button
                        className="w-full"
                        onClick={handleSubmit}
                        disabled={!amount || !date || isSubmitting}
                    >
                        {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        {isSubmitting ? "Generating Contract..." : "Generate & Send Offer"}
                    </Button>
                </CardFooter>
            </Card>

            <div className="hidden lg:block">
                <ContractPreview
                    address={lead.address_street}
                    amount={amount}
                    earnestMoney={earnestMoney}
                    closingDate={date ? format(date, "PPP") : ""}
                />
            </div>
        </div>
    )
}
