"use client"

import { Sidebar } from "@/components/layout/Sidebar";
import { CoPilotSidebar } from "@/components/copilot/CoPilotSidebar";
import { Button } from "@/components/ui/button";
import { Bot } from "lucide-react";
import { useCoPilotStore } from "@/store/copilot-store";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const { toggle, isOpen } = useCoPilotStore();

    return (
        <div className="flex h-screen overflow-hidden bg-background">
            <Sidebar />
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Header */}
                <header className="h-14 border-b border-border bg-background/50 backdrop-blur flex items-center justify-between px-6 shrink-0">
                    <div className="font-semibold text-lg">ARELA Platform <span className="text-xs text-muted-foreground ml-2">v0.2.0</span></div>
                    <Button
                        variant={isOpen ? "secondary" : "outline"}
                        size="sm"
                        onClick={toggle}
                        className="gap-2"
                    >
                        <Bot className="h-4 w-4" />
                        Co-Pilot
                    </Button>
                </header>

                {/* Main Content */}
                <main className="flex-1 overflow-y-auto p-6">
                    {children}
                </main>
            </div>

            {/* Co-Pilot Overlay */}
            <CoPilotSidebar />
        </div>
    );
}
