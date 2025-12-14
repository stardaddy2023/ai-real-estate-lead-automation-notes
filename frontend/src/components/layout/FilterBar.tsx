"use client";

import { useAppStore } from '@/lib/store';
import { Filter, ChevronDown, Search, RefreshCw, Map as MapIcon, List, Handshake, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useState, useRef, useEffect } from 'react';
import AutocompleteInput from '../ui/AutocompleteInput';

export function FilterBar() {
    const {
        searchFilters,
        setSearchFilters,
        fetchScoutedLeads,
        activeZone,
        setActiveZone,
        setViewMode
    } = useAppStore();

    const [isTypeOpen, setIsTypeOpen] = useState(false);
    const typeRef = useRef<HTMLDivElement>(null);

    // Close type dropdown when clicking outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (typeRef.current && !typeRef.current.contains(event.target as Node)) {
                setIsTypeOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleModeChange = (mode: string) => {
        if (mode === 'Leads') {
            setActiveZone('leads');
            setViewMode('list');
        } else if (mode === 'Deals') {
            setActiveZone('deals');
        }
    };

    const getCurrentModeLabel = () => {
        if (activeZone === 'leads') return 'Leads';
        if (activeZone === 'deals') return 'Deals';
        return 'Select Mode';
    };

    const propertyTypes = [
        "Single Family",
        "Multi Family",
        "Condo",
        "Townhouse",
        "Vacant Land",
        "Commercial"
    ];

    const togglePropertyType = (type: string) => {
        const current = searchFilters.property_types;
        const updated = current.includes(type)
            ? current.filter(t => t !== type)
            : [...current, type];
        setSearchFilters({ property_types: updated });
    };

    return (
        <div className="h-16 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 flex items-center px-4 justify-between z-40 relative gap-4">

            {/* Mode Selector */}
            <div className="relative group min-w-[120px]">
                <select
                    value={getCurrentModeLabel()}
                    onChange={(e) => handleModeChange(e.target.value)}
                    className="w-full appearance-none bg-muted/30 border border-input rounded-md py-2 pl-3 pr-8 text-sm font-medium focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer"
                >
                    <option value="Leads">Leads</option>
                    <option value="Deals">Deals</option>
                </select>
                <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
            </div>

            {/* Search Input */}
            <div className="flex-1 max-w-md">
                <AutocompleteInput
                    value={searchFilters.city}
                    onChange={(val) => setSearchFilters({ city: val })}
                    onSearch={() => {
                        const { activeZone, fetchScoutedLeads, filterDeals, searchFilters } = useAppStore.getState();
                        if (activeZone === 'deals') {
                            filterDeals(searchFilters.city);
                        } else {
                            fetchScoutedLeads();
                        }
                    }}
                    placeholder={activeZone === 'deals' ? "Search deals..." : "Search city, zip, or address..."}
                />
            </div>

            {/* Filters Group */}
            <div className="flex items-center space-x-2">

                {/* County Selector */}
                <div className="relative min-w-[100px]">
                    <select
                        value={searchFilters.county}
                        onChange={(e) => setSearchFilters({ county: e.target.value })}
                        className="w-full appearance-none bg-background border border-border rounded-md py-1.5 pl-3 pr-8 text-sm focus:outline-none focus:border-primary cursor-pointer"
                    >
                        <option value="Pima">Pima</option>
                        <option value="Pinal">Pinal</option>
                    </select>
                    <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-muted-foreground pointer-events-none" />
                </div>

                {/* Distress Type */}
                <div className="relative min-w-[140px]">
                    <select
                        value={searchFilters.distress_type}
                        onChange={(e) => setSearchFilters({ distress_type: e.target.value })}
                        className="w-full appearance-none bg-background border border-border rounded-md py-1.5 pl-3 pr-8 text-sm focus:outline-none focus:border-primary cursor-pointer"
                    >
                        <option value="all">Any Distress</option>
                        <option value="code_violations">Code Violations</option>
                        <option value="absentee_owner">Absentee Owner</option>
                    </select>
                    <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-muted-foreground pointer-events-none" />
                </div>

                {/* Limit */}
                <div className="relative min-w-[80px]">
                    <select
                        value={searchFilters.limit}
                        onChange={(e) => setSearchFilters({ limit: parseInt(e.target.value) })}
                        className="w-full appearance-none bg-background border border-border rounded-md py-1.5 pl-3 pr-8 text-sm focus:outline-none focus:border-primary cursor-pointer"
                    >
                        <option value="100">100</option>
                        <option value="500">500</option>
                        <option value="1000">1000</option>
                    </select>
                    <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-muted-foreground pointer-events-none" />
                </div>

                {/* Property Type Dropdown with Checkboxes */}
                <div className="relative" ref={typeRef}>
                    <button
                        onClick={() => setIsTypeOpen(!isTypeOpen)}
                        className={cn(
                            "flex items-center px-3 py-1.5 rounded-md border text-sm transition-all min-w-[100px] justify-between",
                            searchFilters.property_types.length > 0
                                ? "bg-primary/10 border-primary text-primary"
                                : "border-border bg-background hover:border-primary/50"
                        )}
                    >
                        <span className="truncate max-w-[80px]">
                            {searchFilters.property_types.length > 0
                                ? `${searchFilters.property_types.length} Types`
                                : "Type"}
                        </span>
                        <ChevronDown className="w-3 h-3 ml-2 opacity-50" />
                    </button>

                    {isTypeOpen && (
                        <div className="absolute top-full right-0 mt-2 w-48 bg-card border border-border rounded-md shadow-xl z-50 p-2 animate-in fade-in zoom-in-95 duration-200">
                            <div className="space-y-1">
                                {propertyTypes.map((type) => (
                                    <div
                                        key={type}
                                        onClick={() => togglePropertyType(type)}
                                        className="flex items-center px-2 py-1.5 hover:bg-muted rounded cursor-pointer"
                                    >
                                        <div className={cn(
                                            "w-4 h-4 border rounded mr-2 flex items-center justify-center transition-colors",
                                            searchFilters.property_types.includes(type)
                                                ? "bg-primary border-primary text-black"
                                                : "border-muted-foreground"
                                        )}>
                                            {searchFilters.property_types.includes(type) && <Check className="w-3 h-3" />}
                                        </div>
                                        <span className="text-sm">{type}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* View Toggle */}
                <div className="flex bg-muted/30 border border-input rounded-md p-1 items-center">
                    <button
                        onClick={() => setViewMode('list')}
                        className={cn(
                            "p-1.5 rounded-sm transition-all",
                            useAppStore.getState().viewMode === 'list' ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"
                        )}
                        title="List View"
                    >
                        <List className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => setViewMode('map')}
                        className={cn(
                            "p-1.5 rounded-sm transition-all",
                            useAppStore.getState().viewMode === 'map' ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"
                        )}
                        title="Map View"
                    >
                        <MapIcon className="w-4 h-4" />
                    </button>
                </div>

                {/* Search Button */}
                <button
                    onClick={() => {
                        const { activeZone, fetchScoutedLeads, filterDeals, searchFilters } = useAppStore.getState();
                        if (activeZone === 'deals') {
                            filterDeals(searchFilters.city);
                        } else {
                            fetchScoutedLeads();
                        }
                    }}
                    className="px-4 py-1.5 bg-primary text-black font-bold text-sm rounded-md hover:bg-primary/90 transition-all shadow-sm"
                >
                    Search
                </button>
            </div>
        </div>
    );
}
