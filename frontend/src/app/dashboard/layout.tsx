"use client"

import { Sidebar } from "@/components/layout/Sidebar";
import { CoPilotSidebar } from "@/components/copilot/CoPilotSidebar";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex h-screen overflow-hidden bg-background relative">
            {/* Persistent Sidebar */}
            <Sidebar />

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col overflow-hidden relative z-0">
                {/* Main Content */}
                <main className="flex-1 overflow-hidden relative">
                    {children}
                </main>
            </div>

            {/* Co-Pilot Overlay */}
            <CoPilotSidebar />
        </div>
    );
}
