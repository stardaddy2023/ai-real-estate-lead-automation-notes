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

    const [isDistressOpen, setIsDistressOpen] = useState(false);
    const distressRef = useRef<HTMLDivElement>(null);

    const [isTypeOpen, setIsTypeOpen] = useState(false);
    const typeRef = useRef<HTMLDivElement>(null);

    // Close dropdowns when clicking outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (typeRef.current && !typeRef.current.contains(event.target as Node)) {
                setIsTypeOpen(false);
            }
            if (distressRef.current && !distressRef.current.contains(event.target as Node)) {
                setIsDistressOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    // Mode selector logic removed


    const propertyTypes = [
        "Single Family",
        "Multi Family",
        "Condo",
        "Townhouse",
        "Vacant Land",
        "Commercial"
    ];

    const distressTypes = [
        { value: "code_violations", label: "Code Violations" },
        { value: "absentee_owner", label: "Absentee Owner" },
        // Add more as backend supports them
    ];

    const togglePropertyType = (type: string) => {
        const current = searchFilters.property_types;
        const updated = current.includes(type)
            ? current.filter(t => t !== type)
            : [...current, type];
        setSearchFilters({ property_types: updated });
    };

    const toggleDistressType = (type: string) => {
        const current = searchFilters.distress_type;

        if (type === 'all') {
            // If selecting 'all', clear others
            setSearchFilters({ distress_type: ['all'] });
            return;
        }

        let updated: string[];
        if (current.includes('all')) {
            // If 'all' was selected and we pick a specific one, remove 'all' and add specific
            updated = [type];
        } else {
            updated = current.includes(type)
                ? current.filter(t => t !== type)
                : [...current, type];
        }

        // If nothing selected, default back to 'all' (or empty? User said default words "Distress Type")
        // Actually, let's allow empty to mean "None selected" which implies "Show me nothing"? 
        // Or "Generic Search"? 
        // Usually empty filter means "All". But we have an explicit "All".
        // Let's enforce at least one selection or default to 'all' if empty?
        if (updated.length === 0) {
            updated = ['all'];
        }

        setSearchFilters({ distress_type: updated });
    };

    const formatDistressLabel = (val: string) => {
        if (val === 'all') return "Any Distress";
        const found = distressTypes.find(d => d.value === val);
        return found ? found.label : val;
    };

    return (
        <div className="h-16 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 flex items-center px-4 justify-between z-40 relative gap-4">

            {/* Mode Selector Removed */}

            {/* Search Input */}
            <div className="flex-1 max-w-md">
                <AutocompleteInput
                    value={searchFilters.city}
                    onChange={(val) => setSearchFilters({ city: val })}
                    onSearch={() => {
                        const { activeZone, fetchScoutedLeads, filterDeals, searchFilters } = useAppStore.getState();
                        if (activeZone === 'crm') {
                            filterDeals(searchFilters.city);
                        } else {
                            fetchScoutedLeads();
                        }
                    }}
                    placeholder={activeZone === 'crm' ? "Search properties..." : "Search Address, City, Zip, or County..."}
                />
            </div>

            {/* Filters Group */}
            <div className="flex items-center space-x-2">

                {/* Distress Type Dropdown with Checkboxes */}
                <div className="relative" ref={distressRef}>
                    <button
                        onClick={() => setIsDistressOpen(!isDistressOpen)}
                        className={cn(
                            "flex items-center px-3 py-1.5 rounded-md border text-sm transition-all min-w-[140px] justify-between",
                            searchFilters.distress_type.length > 0 && !searchFilters.distress_type.includes('all')
                                ? "bg-red-500/10 border-red-500 text-red-500"
                                : "border-border bg-background hover:border-primary/50"
                        )}
                    >
                        <span className="truncate max-w-[120px]">
                            {searchFilters.distress_type.includes('all') || searchFilters.distress_type.length === 0
                                ? "Distress Type"
                                : searchFilters.distress_type.length === 1
                                    ? formatDistressLabel(searchFilters.distress_type[0])
                                    : `${searchFilters.distress_type.length} Selected`}
                        </span>
                        <ChevronDown className="w-3 h-3 ml-2 opacity-50" />
                    </button>

                    {isDistressOpen && (
                        <div className="absolute top-full left-0 mt-2 w-56 bg-card border border-border rounded-md shadow-xl z-50 p-2 animate-in fade-in zoom-in-95 duration-200">
                            <div className="space-y-1">
                                <div
                                    onClick={() => toggleDistressType('all')}
                                    className="flex items-center px-2 py-1.5 hover:bg-muted rounded cursor-pointer"
                                >
                                    <div className={cn(
                                        "w-4 h-4 border rounded mr-2 flex items-center justify-center transition-colors",
                                        searchFilters.distress_type.includes('all')
                                            ? "bg-primary border-primary text-black"
                                            : "border-muted-foreground"
                                    )}>
                                        {searchFilters.distress_type.includes('all') && <Check className="w-3 h-3" />}
                                    </div>
                                    <span className="text-sm">Any Distress</span>
                                </div>
                                <div className="h-px bg-border my-1" />
                                {distressTypes.map((type) => (
                                    <div
                                        key={type.value}
                                        onClick={() => toggleDistressType(type.value)}
                                        className="flex items-center px-2 py-1.5 hover:bg-muted rounded cursor-pointer"
                                    >
                                        <div className={cn(
                                            "w-4 h-4 border rounded mr-2 flex items-center justify-center transition-colors",
                                            searchFilters.distress_type.includes(type.value)
                                                ? "bg-primary border-primary text-black"
                                                : "border-muted-foreground"
                                        )}>
                                            {searchFilters.distress_type.includes(type.value) && <Check className="w-3 h-3" />}
                                        </div>
                                        <span className="text-sm">{type.label}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Limit */}
                <div className="relative min-w-[80px]">
                    <select
                        value={searchFilters.limit}
                        onChange={(e) => setSearchFilters({ limit: parseInt(e.target.value) })}
                        className="w-full appearance-none bg-background border border-border rounded-md py-1.5 pl-3 pr-8 text-sm focus:outline-none focus:border-primary cursor-pointer"
                    >
                        <option value="10">10</option>
                        <option value="25">25</option>
                        <option value="50">50</option>
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
                        <span className="truncate max-w-[120px]">
                            {searchFilters.property_types.length === 0
                                ? "Type"
                                : searchFilters.property_types.length === 1
                                    ? searchFilters.property_types[0]
                                    : `${searchFilters.property_types.length} Types`}
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
                        if (activeZone === 'crm') {
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
