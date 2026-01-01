"use client";

import { useAppStore } from '@/lib/store';
import {
    Map,
    Building2,
    Users,
    MessageSquare,
    BarChart3,
    Settings,
    Hexagon,
    Search,
    Handshake,
    Inbox,
    Database,
    ChevronLeft,
    ChevronRight,
    Bot
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useState } from 'react';
import { useCoPilotStore } from '@/store/copilot-store';

const navItems = [
    { id: 'market_scout', icon: BarChart3, label: 'Market Recon' },
    { id: 'leads', icon: Search, label: 'Lead Scout' },
    { id: 'my_leads', icon: Inbox, label: 'Lead Inbox' },
    { id: 'recorder', icon: Database, label: 'Recorder' },
    { id: 'crm', icon: Building2, label: 'Property Sniper' },
    { id: 'contacts', icon: Users, label: 'Contacts' },
    { id: 'campaigns', icon: MessageSquare, label: 'Campaigns' },
    { id: 'analytics', icon: BarChart3, label: 'Watchtower' },
    { id: 'settings', icon: Settings, label: 'Settings' },
] as const;

export function Sidebar() {
    const { activeZone, setActiveZone } = useAppStore();
    const [isCollapsed, setIsCollapsed] = useState(false);
    const { toggle: toggleCoPilot, isOpen: isCoPilotOpen } = useCoPilotStore();

    return (
        <div
            className={cn(
                "h-full bg-background border-r border-border flex flex-col relative transition-all duration-300 ease-in-out z-40",
                isCollapsed ? "w-16" : "w-64"
            )}
        >
            {/* Toggle Tab */}
            <button
                onClick={() => setIsCollapsed(!isCollapsed)}
                className="absolute -right-3 top-20 bg-card border border-border rounded-full p-1 shadow-md hover:bg-accent text-muted-foreground hover:text-foreground z-50"
            >
                {isCollapsed ? <ChevronRight className="w-3 h-3" /> : <ChevronLeft className="w-3 h-3" />}
            </button>

            {/* Logo Area */}
            <div className={cn(
                "h-16 flex items-center border-b border-border bg-card/50 backdrop-blur-sm overflow-hidden whitespace-nowrap",
                isCollapsed ? "justify-center px-0" : "px-6"
            )}>
                <Hexagon className="w-8 h-8 text-primary animate-pulse shrink-0" />
                <span className={cn(
                    "ml-3 font-bold text-xl tracking-wider text-foreground transition-opacity duration-200",
                    isCollapsed ? "opacity-0 w-0" : "opacity-100"
                )}>
                    ARELA
                </span>
            </div>

            {/* Navigation */}
            <nav className="flex-1 py-6 space-y-2 px-2 overflow-y-auto overflow-x-hidden">
                {/* Co-Pilot Button (Special Toggle) */}
                <button
                    onClick={toggleCoPilot}
                    title={isCollapsed ? "Co-Pilot" : undefined}
                    className={cn(
                        "w-full flex items-center p-2 rounded-md transition-all duration-200 group relative overflow-hidden mb-4",
                        isCoPilotOpen
                            ? "bg-blue-500/10 text-blue-500 border border-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.1)]"
                            : "text-muted-foreground hover:text-foreground hover:bg-muted/50",
                        isCollapsed ? "justify-center" : ""
                    )}
                >
                    {isCoPilotOpen && (
                        <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500 shadow-[0_0_10px_#3b82f6]" />
                    )}

                    <Bot className={cn("w-5 h-5 shrink-0", isCoPilotOpen && "animate-pulse")} />

                    <span className={cn(
                        "ml-3 font-medium tracking-wide whitespace-nowrap transition-all duration-200",
                        isCollapsed ? "opacity-0 w-0 hidden" : "opacity-100"
                    )}>
                        Co-Pilot
                    </span>

                    {/* Hover Glow Effect */}
                    {!isCollapsed && (
                        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/0 via-blue-500/5 to-blue-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
                    )}
                </button>

                <div className="h-px bg-border/50 mx-2 mb-4" />

                {navItems.map((item) => {
                    const isActive = activeZone === item.id;
                    return (
                        <button
                            key={item.id}
                            onClick={() => setActiveZone(item.id as any)}
                            title={isCollapsed ? item.label : undefined}
                            className={cn(
                                "w-full flex items-center p-2 rounded-md transition-all duration-200 group relative overflow-hidden",
                                isActive
                                    ? "bg-primary/10 text-primary border border-primary/20 shadow-[0_0_15px_rgba(0,255,128,0.1)]"
                                    : "text-muted-foreground hover:text-foreground hover:bg-muted/50",
                                isCollapsed ? "justify-center" : ""
                            )}
                        >
                            {isActive && (
                                <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary shadow-[0_0_10px_#00ff80]" />
                            )}

                            <item.icon className={cn("w-5 h-5 shrink-0", isActive && "animate-pulse")} />

                            <span className={cn(
                                "ml-3 font-medium tracking-wide whitespace-nowrap transition-all duration-200",
                                isCollapsed ? "opacity-0 w-0 hidden" : "opacity-100"
                            )}>
                                {item.label}
                            </span>

                            {/* Hover Glow Effect */}
                            {!isCollapsed && (
                                <div className="absolute inset-0 bg-gradient-to-r from-primary/0 via-primary/5 to-primary/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
                            )}
                        </button>
                    );
                })}
            </nav>

            {/* User Status */}
            <div className="p-4 border-t border-border bg-card/30 overflow-hidden whitespace-nowrap">
                <div className={cn("flex items-center", isCollapsed ? "justify-center" : "")}>
                    <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary to-accent flex items-center justify-center text-xs font-bold text-black border border-white/20 shrink-0">
                        OP
                    </div>
                    <div className={cn("ml-3 transition-opacity duration-200", isCollapsed ? "opacity-0 w-0 hidden" : "opacity-100")}>
                        <p className="text-sm font-bold text-foreground">Operator</p>
                        <p className="text-xs text-primary">System Online</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
