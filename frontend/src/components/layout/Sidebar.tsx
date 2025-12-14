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
    Handshake
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
    { id: 'market_scout', icon: BarChart3, label: 'Market Scout' },
    { id: 'leads', icon: Search, label: 'Lead Scout' },
    { id: 'deals', icon: Handshake, label: 'Deals' },
    { id: 'crm', icon: Building2, label: 'My Properties' },
    { id: 'contacts', icon: Users, label: 'Contacts' },
    { id: 'campaigns', icon: MessageSquare, label: 'Campaigns' },
    { id: 'analytics', icon: BarChart3, label: 'Watchtower' },
    { id: 'settings', icon: Settings, label: 'Settings' },
] as const;

export function Sidebar() {
    const { activeZone, setActiveZone } = useAppStore();

    return (
        <aside className="w-20 lg:w-64 h-screen bg-background border-r border-border flex flex-col z-50 relative">
            {/* Logo Area */}
            <div className="h-16 flex items-center px-6 border-b border-border bg-card/50 backdrop-blur-sm">
                <Hexagon className="w-8 h-8 text-primary animate-pulse" />
                <span className="ml-3 font-bold text-xl tracking-wider hidden lg:block text-foreground">
                    ARELA
                </span>
            </div>

            {/* Navigation */}
            <nav className="flex-1 py-6 space-y-2 px-3">
                {navItems.map((item) => {
                    const isActive = activeZone === item.id;
                    return (
                        <button
                            key={item.id}
                            onClick={() => setActiveZone(item.id)}
                            className={cn(
                                "w-full flex items-center p-3 rounded-md transition-all duration-200 group relative overflow-hidden",
                                isActive
                                    ? "bg-primary/10 text-primary border border-primary/20 shadow-[0_0_15px_rgba(0,255,128,0.1)]"
                                    : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                            )}
                        >
                            {isActive && (
                                <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary shadow-[0_0_10px_#00ff80]" />
                            )}

                            <item.icon className={cn("w-5 h-5", isActive && "animate-pulse")} />

                            <span className="ml-3 font-medium hidden lg:block tracking-wide">
                                {item.label}
                            </span>

                            {/* Hover Glow Effect */}
                            <div className="absolute inset-0 bg-gradient-to-r from-primary/0 via-primary/5 to-primary/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
                        </button>
                    );
                })}
            </nav>

            {/* User Status */}
            <div className="p-4 border-t border-border bg-card/30">
                <div className="flex items-center">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary to-accent flex items-center justify-center text-xs font-bold text-black border border-white/20">
                        OP
                    </div>
                    <div className="ml-3 hidden lg:block">
                        <p className="text-sm font-bold text-foreground">Operator</p>
                        <p className="text-xs text-primary">System Online</p>
                    </div>
                </div>
            </div>
        </aside>
    );
}
