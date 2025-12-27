import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ImageIcon } from "lucide-react"

export function DealPhotos() {
    return (
        <Card className="h-full">
            <CardHeader>
                <CardTitle>Property Photos</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-2 gap-2">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="aspect-square bg-muted rounded-md flex items-center justify-center">
                            <ImageIcon className="h-8 w-8 text-muted-foreground/50" />
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    )
}
