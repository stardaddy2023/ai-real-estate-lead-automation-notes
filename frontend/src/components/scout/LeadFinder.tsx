"use client";

import { useState, useEffect } from 'react';
import { Search, Download, Filter, Loader2, CheckCircle, AlertCircle, Map as MapIcon, List } from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { InteractiveMap } from '@/components/map/InteractiveMap';
import { cn } from '@/lib/utils';

interface ScoutedLead {
    source: string;
    address: string;
    owner_name?: string;
    mailing_address?: string;
    distress_signals?: string[];
    sqft?: number;
    year_built?: number;
    status: string;
    strategy: string;
    zoning?: string;
    property_type?: string;
    lot_size?: number;
    estimated_value?: number;
    parcel_id?: string;
    last_sale_date?: string;
    last_sale_price?: number;
    latitude?: number;
    longitude?: number;
    distress_score?: number;
}

interface LeadFinderProps {
    defaultView?: 'list' | 'map';
}

export function LeadFinder({ defaultView = 'map' }: LeadFinderProps) {
    const { setSelectedProperty, toggleDetailPanel, fetchLeads, scoutedLeads, fetchScoutedLeads, viewMode, setViewMode } = useAppStore();
    const [isLoading, setIsLoading] = useState(false);
    const [selectedLeads, setSelectedLeads] = useState<Set<string>>(new Set());
    const [importStatus, setImportStatus] = useState<{ imported: number; updated: number } | null>(null);

    const handleImport = async () => {
        if (selectedLeads.size === 0) return;

        setIsLoading(true);
        try {
            const leadsToImport = scoutedLeads.filter((l: any) => selectedLeads.has(l.address));

            const res = await fetch('http://127.0.0.1:8000/scout/import', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(leadsToImport)
            });

            if (!res.ok) throw new Error('Import failed');

            const status = await res.json();
            setImportStatus(status);

            // Refresh global leads list
            await fetchLeads();

            // Clear selection after successful import
            setSelectedLeads(new Set());

        } catch (error) {
            console.error("Import error:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const toggleSelectAll = () => {
        if (selectedLeads.size === scoutedLeads.length) {
            setSelectedLeads(new Set());
        } else {
            setSelectedLeads(new Set(scoutedLeads.map((r: any) => r.address)));
        }
    };

    const toggleSelect = (address: string) => {
        const newSet = new Set(selectedLeads);
        if (newSet.has(address)) {
            newSet.delete(address);
        } else {
            newSet.add(address);
        }
        setSelectedLeads(newSet);
    };

    const handleRowClick = (lead: ScoutedLead) => {
        // Cast to any to match store type for now, or ensure compatibility
        setSelectedProperty(lead as any);
        toggleDetailPanel(true);
    };

    return (
        <div className="h-full flex flex-col bg-background text-foreground">
            {/* List View Header */}
            {viewMode === 'list' && (
                <>
                    <div className="p-6 border-b border-border bg-card/50 flex justify-between items-start">
                        <div>
                            <h1 className="text-2xl font-bold tracking-tight flex items-center">
                                <Search className="w-6 h-6 mr-3 text-primary" />
                                Lead Scout
                            </h1>
                            <p className="text-muted-foreground mt-1">
                                Search public records for distressed properties and import them into your pipeline.
                            </p>
                        </div>
                    </div>

                    {scoutedLeads.length > 0 && (
                        <div className="p-3 bg-primary/5 border-b border-primary/20 flex items-center justify-between">
                            <div className="flex items-center space-x-4">
                                <span className="text-sm font-bold text-primary">Found {scoutedLeads.length} leads</span>
                                <div className="h-4 w-px bg-border" />
                                <span className="text-sm text-muted-foreground">{selectedLeads.size} selected</span>
                            </div>
                            <div className="flex items-center space-x-3">
                                {importStatus && (
                                    <span className="text-sm text-green-500 flex items-center mr-4 animate-in fade-in">
                                        <CheckCircle className="w-4 h-4 mr-1" />
                                        Imported {importStatus.imported}, Updated {importStatus.updated}
                                    </span>
                                )}
                                <button
                                    onClick={handleImport}
                                    disabled={selectedLeads.size === 0 || isLoading}
                                    className="px-4 py-1.5 bg-green-500 text-black font-bold text-sm rounded hover:bg-green-400 transition-colors flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <Download className="w-4 h-4 mr-2" />
                                    Import Selected
                                </button>
                            </div>
                        </div>
                    )}
                </>
            )}

            {/* Map View Floating Header */}
            {viewMode === 'map' && (
                <div className="absolute top-20 left-4 right-4 z-10 pointer-events-none flex justify-between items-start">
                    {/* Title Card */}
                    <div
                        onClick={() => setViewMode('list')}
                        className="pointer-events-auto bg-card/90 backdrop-blur border border-border rounded-lg shadow-lg px-4 py-2 flex items-center cursor-pointer hover:bg-card/100 transition-colors"
                    >
                        <Search className="w-5 h-5 mr-3 text-primary" />
                        <div>
                            <h1 className="font-bold text-sm">Lead Scout</h1>
                            <p className="text-xs text-muted-foreground">{scoutedLeads.length} Leads Found</p>
                        </div>
                    </div>

                    {/* Actions Card */}
                    {scoutedLeads.length > 0 && (
                        <div className="pointer-events-auto bg-card/90 backdrop-blur border border-border rounded-lg shadow-lg p-2 flex items-center space-x-3">
                            <span className="text-xs text-muted-foreground ml-2">{selectedLeads.size} selected</span>
                            <button
                                onClick={handleImport}
                                disabled={selectedLeads.size === 0 || isLoading}
                                className="px-3 py-1.5 bg-green-500 text-black font-bold text-xs rounded hover:bg-green-400 transition-colors flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Download className="w-3 h-3 mr-1.5" />
                                Import
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* Content Area */}
            <div className="flex-1 overflow-hidden relative">
                {viewMode === 'map' ? (
                    <div className="absolute inset-0">
                        <InteractiveMap
                            leads={scoutedLeads.map((r: any) => ({ ...r, id: r.address, score: r.distress_score || 0 }))}
                            onSelect={handleRowClick}
                        />
                    </div>
                ) : (
                    <div className="h-full overflow-auto">
                        {scoutedLeads.length === 0 && !isLoading ? (
                            <div className="h-full flex flex-col items-center justify-center text-muted-foreground opacity-50">
                                <Filter className="w-12 h-12 mb-4" />
                                <p>Use the top bar to search for leads</p>
                            </div>
                        ) : (
                            <table className="w-full text-sm text-left">
                                <thead className="text-xs text-muted-foreground uppercase bg-muted/50 sticky top-0 backdrop-blur-sm z-10">
                                    <tr>
                                        <th className="p-4 w-10">
                                            <input
                                                type="checkbox"
                                                checked={scoutedLeads.length > 0 && selectedLeads.size === scoutedLeads.length}
                                                onChange={toggleSelectAll}
                                                className="rounded border-border bg-background"
                                            />
                                        </th>
                                        <th className="p-4">Address</th>
                                        <th className="p-4">Owner</th>
                                        <th className="p-4">Type</th>
                                        <th className="p-4">Sqft</th>
                                        <th className="p-4">Lot (Acres)</th>
                                        <th className="p-4">Value</th>
                                        <th className="p-4">Last Sale</th>
                                        <th className="p-4">Distress</th>
                                        <th className="p-4">Source</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                    {scoutedLeads.map((lead: any, idx: number) => (
                                        <tr
                                            key={idx}
                                            onClick={() => handleRowClick(lead)}
                                            className="hover:bg-muted/30 transition-colors group cursor-pointer"
                                        >
                                            <td className="p-4" onClick={(e) => e.stopPropagation()}>
                                                <input
                                                    type="checkbox"
                                                    checked={selectedLeads.has(lead.address)}
                                                    onChange={() => toggleSelect(lead.address)}
                                                    className="rounded border-border bg-background"
                                                />
                                            </td>
                                            <td className="p-4 font-mono">
                                                <div className="font-bold">{lead.address}</div>
                                                <div className="text-xs text-muted-foreground">APN: {lead.parcel_id}</div>
                                                <div className="text-xs text-muted-foreground">Zoning: {lead.zoning}</div>
                                            </td>
                                            <td className="p-4">
                                                <div>{lead.owner_name || <span className="text-muted-foreground italic">Unknown</span>}</div>
                                                <div className="text-xs text-muted-foreground truncate max-w-[150px]">{lead.mailing_address}</div>
                                            </td>
                                            <td className="p-4 text-xs max-w-[150px] truncate" title={lead.property_type}>{lead.property_type || '-'}</td>
                                            <td className="p-4">{lead.sqft ? lead.sqft.toLocaleString() : '-'}</td>
                                            <td className="p-4">{lead.lot_size ? lead.lot_size.toFixed(2) : '-'}</td>
                                            <td className="p-4">{lead.estimated_value ? `$${lead.estimated_value.toLocaleString()}` : '-'}</td>
                                            <td className="p-4">
                                                <div>{lead.last_sale_date || '-'}</div>
                                                {lead.last_sale_price && <div className="text-xs text-muted-foreground">${lead.last_sale_price.toLocaleString()}</div>}
                                            </td>
                                            <td className="p-4">
                                                {lead.distress_signals?.map((s: string, i: number) => (
                                                    <span key={i} className="inline-block px-2 py-0.5 bg-red-500/10 text-red-500 rounded text-xs mr-1 border border-red-500/20">
                                                        {s}
                                                    </span>
                                                ))}
                                            </td>
                                            <td className="p-4 text-xs text-muted-foreground">{lead.source}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
