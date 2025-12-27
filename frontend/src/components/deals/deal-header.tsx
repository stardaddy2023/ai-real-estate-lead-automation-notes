import { Lead } from "@/types"
import { Badge } from "@/components/ui/badge"

interface DealHeaderProps {
    lead: Lead
}

export function DealHeader({ lead }: DealHeaderProps) {
    let colorClass = "bg-slate-100 text-slate-800"
    if (lead.status === "new") colorClass = "bg-blue-100 text-blue-800"
    else if (lead.status === "contacted") colorClass = "bg-yellow-100 text-yellow-800"
    else if (lead.status === "offer_made") colorClass = "bg-green-100 text-green-800"

    return (
        <div className="flex items-center justify-between">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">{lead.address_street}</h1>
                <p className="text-muted-foreground">{lead.address_zip}</p>
            </div>
            <div className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-semibold ${colorClass}`}>
                {lead.status}
            </div>
        </div>
    )
}
