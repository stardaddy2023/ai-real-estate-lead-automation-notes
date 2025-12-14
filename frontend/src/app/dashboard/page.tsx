"use client";

import { Sidebar } from '@/components/layout/Sidebar';
import { PropertyPanel } from '@/components/property/PropertyPanel';
import { useEffect, useState } from 'react';
import { InteractiveMap } from '@/components/map/InteractiveMap';
import { LeadList } from '@/components/dashboard/LeadList';
import { FilterBar } from '@/components/layout/FilterBar';
import { useAppStore } from '@/lib/store';
import { AddLeadDialog } from '@/components/dashboard/AddLeadDialog';
import { MarketScout } from '@/components/scout/MarketScout';
import { LeadFinder } from '@/components/scout/LeadFinder';
import { DealsBoard } from '@/components/deals/DealsBoard';
import { Plus, Map as MapIcon, List } from 'lucide-react';
import { cn } from '@/lib/utils';
import { APIProvider } from '@vis.gl/react-google-maps';

export default function DashboardPage() {
    const { setSelectedProperty, activeZone, leads, fetchLeads, viewMode, setViewMode } = useAppStore();
    const [isAddLeadOpen, setIsAddLeadOpen] = useState(false);
    const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "";

    useEffect(() => {
        fetchLeads();
    }, [fetchLeads]);

    if (!apiKey) return <div className="flex items-center justify-center h-screen text-red-500">Missing Google Maps API Key</div>;

    return (
        <APIProvider apiKey={apiKey} libraries={['places']}>
            <div className="flex h-screen w-full bg-background text-foreground overflow-hidden font-sans">
                <Sidebar />

                <div className="flex-1 flex flex-col relative">
                    {/* Header Overlay */}
                    <div className="absolute top-0 left-0 right-0 z-10 p-4 pointer-events-none">
                        <div className="flex items-center justify-between">
                            <div className="pointer-events-auto">
                                <FilterBar />
                            </div>
                            <div className="pointer-events-auto flex items-center space-x-2">
                                {/* View Toggle */}
                                {(activeZone === 'deals' || activeZone === 'crm') && (
                                    <div className="bg-background/95 backdrop-blur border border-border rounded-md p-1 flex items-center shadow-lg">
                                        <button
                                            onClick={() => setViewMode('map')}
                                            className={cn(
                                                "p-2 rounded-sm transition-all",
                                                viewMode === 'map' ? "bg-primary text-black shadow-sm" : "text-muted-foreground hover:text-foreground"
                                            )}
                                            title="Map View"
                                        >
                                            <MapIcon className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => setViewMode('list')}
                                            className={cn(
                                                "p-2 rounded-sm transition-all",
                                                viewMode === 'list' ? "bg-primary text-black shadow-sm" : "text-muted-foreground hover:text-foreground"
                                            )}
                                            title="List View"
                                        >
                                            <List className="w-4 h-4" />
                                        </button>
                                    </div>
                                )}

                                <button
                                    onClick={() => setIsAddLeadOpen(true)}
                                    className="flex items-center px-4 py-2 bg-primary text-black font-bold rounded-md shadow-lg hover:bg-primary/90 transition-all h-[42px]"
                                >
                                    <Plus className="w-4 h-4 mr-2" />
                                    Add Lead
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Main Content Layer */}
                    <div className="flex-1 relative z-0 overflow-hidden">
                        {activeZone === 'leads' ? (
                            <LeadFinder defaultView="list" />

                        ) : activeZone === 'market_scout' ? (
                            <MarketScout />
                        ) : activeZone === 'deals' ? (
                            <DealsBoard
                                leads={useAppStore.getState().filteredLeads}
                                onSelect={setSelectedProperty}
                                viewMode={viewMode}
                            />
                        ) : (
                            // Default fallback
                            <DealsBoard
                                leads={useAppStore.getState().filteredLeads}
                                onSelect={setSelectedProperty}
                                viewMode={viewMode}
                            />
                        )}
                    </div>

                    {/* Side Panel - Hide in full-screen tools except leads/scout/deals */}
                    {activeZone !== 'market_scout' && <PropertyPanel />}

                    {/* Modals */}
                    <AddLeadDialog isOpen={isAddLeadOpen} onClose={() => setIsAddLeadOpen(false)} />
                </div>
            </div>
        </APIProvider>
    );
}
