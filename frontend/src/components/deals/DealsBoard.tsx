import { useState } from 'react';
import { Handshake, Map as MapIcon, List } from 'lucide-react';
import { InteractiveMap } from '@/components/map/InteractiveMap';
import { LeadList } from '@/components/dashboard/LeadList';
import { cn } from '@/lib/utils';

import { useAppStore } from '@/lib/store';

interface DealsBoardProps {
    leads: any[];
    onSelect: (lead: any) => void;
    viewMode: 'map' | 'list';
}

export function DealsBoard({ leads, onSelect, viewMode }: DealsBoardProps) {
    const { setViewMode } = useAppStore();

    return (
        <div className="h-full flex flex-col bg-background text-foreground relative">
            {/* Header Overlay (Absolute to float over map) */}
            <div className="absolute top-20 left-4 right-4 z-10 pointer-events-none">
                <div className="flex items-center justify-between">
                    <div
                        onClick={() => setViewMode('list')}
                        className="pointer-events-auto bg-card/90 backdrop-blur border border-border rounded-lg shadow-lg px-4 py-2 flex items-center cursor-pointer hover:bg-card/100 transition-colors"
                    >
                        <Handshake className="w-5 h-5 mr-3 text-primary" />
                        <div>
                            <h1 className="font-bold text-sm">Deals Pipeline</h1>
                            <p className="text-xs text-muted-foreground">{leads.length} Active Leads</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 relative z-0 overflow-hidden">
                {viewMode === 'map' ? (
                    <InteractiveMap
                        leads={leads}
                        onSelect={onSelect}
                    />
                ) : (
                    <div className="h-full pt-20 px-4 pb-4 overflow-hidden flex flex-col">
                        {/* Add padding top to account for absolute header */}
                        <div className="flex-1 bg-card border border-border rounded-lg overflow-hidden shadow-sm">
                            <LeadList
                                leads={leads}
                                onSelect={onSelect}
                            />
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
