import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface ContractPreviewProps {
    address: string
    amount: string
    earnestMoney: string
    closingDate: string
    buyerName?: string
}

export function ContractPreview({
    address,
    amount,
    earnestMoney,
    closingDate,
    buyerName = "ARELA AI",
}: ContractPreviewProps) {
    const amountFormatted = amount ? `$${parseInt(amount).toLocaleString()}` : "___"
    const earnestFormatted = earnestMoney ? `$${parseInt(earnestMoney).toLocaleString()}` : "___"
    const dateFormatted = closingDate || "___"

    return (
        <Card className="h-full bg-muted/50">
            <CardHeader>
                <CardTitle className="text-sm font-medium text-muted-foreground">Contract Preview</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="prose prose-sm dark:prose-invert max-w-none font-mono text-xs p-4 bg-background border rounded-md whitespace-pre-wrap">
                    PURCHASE AND SALE AGREEMENT

                    1. PARTIES: This agreement is made between {buyerName} ("Buyer") and the Owner of Record ("Seller").

                    2. PROPERTY: Buyer agrees to purchase the property located at:
                    {address}

                    3. PURCHASE PRICE: The total purchase price shall be {amountFormatted}.

                    4. EARNEST MONEY: Buyer shall deposit {earnestFormatted} as earnest money with the Closing Agent upon acceptance.

                    5. CLOSING: This transaction shall close on or before {dateFormatted}.

                    6. TERMS: Cash transaction. Sold "As-Is". Buyer pays all closing costs.

                    [... Standard Clauses ...]

                    ________________________
                    Buyer Signature
                </div>
            </CardContent>
        </Card>
    )
}
