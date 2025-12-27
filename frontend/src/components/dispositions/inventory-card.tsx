import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Lead } from "@/types"

interface InventoryCardProps {
    lead: Lead
}

export function InventoryCard({ lead }: InventoryCardProps) {
    // Mock financial data for now since it's not in the Lead interface yet
    const contractPrice = 120000
    const arv = 180000
    const repairs = 25000
    const expectedProfit = arv - repairs - contractPrice

    return (
        <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
            <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                    <CardTitle className="text-lg font-bold">{lead.address_street}</CardTitle>
                    <Badge variant="outline" className="bg-green-100 text-green-800 border-green-200">
                        For Sale
                    </Badge>
                </div>
                <p className="text-sm text-muted-foreground">{lead.address_zip}</p>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <p className="text-muted-foreground">Contract Price</p>
                        <p className="font-semibold">${contractPrice.toLocaleString()}</p>
                    </div>
                    <div>
                        <p className="text-muted-foreground">Est. Profit</p>
                        <p className="font-bold text-green-600">${expectedProfit.toLocaleString()}</p>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
