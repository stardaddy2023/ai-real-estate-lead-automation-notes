import { create } from 'zustand';

interface Property {
    id: number;
    address: string;
    status: string;
    strategy: string;
    distress_score?: number;
    score?: number; // Keep for backward compatibility if needed
    reasoning?: string;
    latitude?: number;
    longitude?: number;
    location?: { lat: number; lng: number }; // Keep for backward compatibility
    phone?: string;
    email?: string;
    owner_name?: string;
    mailing_address?: string;
    social_ids?: { [key: string]: string };
    bedrooms?: number;
    bathrooms?: number;
    sqft?: number;
    lot_size?: number;
    year_built?: number;
    has_pool?: string;
    has_garage?: string;
    has_guesthouse?: string;
    last_sale_date?: string;
    last_sale_price?: number;
    offer_amount?: number;
    parcel_id?: string;
}

interface AppState {
    selectedProperty: Property | null;
    isFilterOpen: boolean;
    isDetailPanelOpen: boolean;
    activeZone: 'market_scout' | 'leads' | 'my_leads' | 'deals' | 'crm' | 'contacts' | 'campaigns' | 'analytics' | 'settings';
    leads: Property[];
    filteredLeads: Property[]; // Add filteredLeads to interface
    viewMode: 'map' | 'list';

    setSelectedProperty: (property: Property | null) => void;
    toggleFilter: () => void;
    toggleDetailPanel: (isOpen: boolean) => void;
    setActiveZone: (zone: AppState['activeZone']) => void;
    setViewMode: (mode: 'map' | 'list') => void;
    fetchLeads: () => Promise<void>;
    filterDeals: (query: string) => void; // Add filterDeals to interface

    // Scout State
    scoutedLeads: any[]; // Using any for now to avoid circular dependency, or duplicate interface
    searchFilters: {
        city: string;
        zip_code: string;
        county: string; // Add county
        distress_type: string[];
        property_types: string[];
        limit: number;
    };
    setSearchFilters: (filters: Partial<AppState['searchFilters']>) => void;
    fetchScoutedLeads: () => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
    selectedProperty: null,
    isFilterOpen: false,
    isDetailPanelOpen: false,
    activeZone: 'market_scout',
    leads: [],
    filteredLeads: [], // Initialize filteredLeads
    viewMode: 'map',

    // Scout State Initial Values
    scoutedLeads: [],
    searchFilters: {
        city: '',
        zip_code: '',
        county: 'Pima', // Default to Pima
        distress_type: ['all'],
        property_types: ['Single Family'],
        limit: 100
    },

    setSelectedProperty: (property) => set({ selectedProperty: property, isDetailPanelOpen: !!property }),
    toggleFilter: () => set((state) => ({ isFilterOpen: !state.isFilterOpen })),
    toggleDetailPanel: (isOpen) => set({ isDetailPanelOpen: isOpen }),
    setActiveZone: (zone) => set({ activeZone: zone }),
    setViewMode: (mode) => set({ viewMode: mode }),

    setSearchFilters: (filters) => set((state) => ({
        searchFilters: { ...state.searchFilters, ...filters }
    })),

    fetchLeads: async () => {
        try {
            const res = await fetch('http://127.0.0.1:8000/leads');
            const data = await res.json();
            set({ leads: data, filteredLeads: data }); // Initialize filteredLeads with all leads
        } catch (error) {
            console.error("Failed to fetch leads:", error);
        }
    },


    fetchScoutedLeads: async () => {
        const { searchFilters } = get();
        try {
            // Parse the input (stored in city) to determine if it's a city, zip, address, or county
            const searchInput = searchFilters.city.trim();
            const upperInput = searchInput.toUpperCase();
            const isZip = /^\d{5}$/.test(searchInput);

            // Check for County
            let county = 'Pima'; // Default
            if (upperInput.includes('PINAL')) {
                county = 'Pinal';
            } else if (upperInput.includes('PIMA')) {
                county = 'Pima';
            }

            // List of known Pima County cities/CDPs to prioritize as City search
            const knownCities = ['TUCSON', 'MARANA', 'ORO VALLEY', 'SAHUARITA', 'VAIL', 'CATALINA', 'GREEN VALLEY', 'SOUTH TUCSON'];
            const isCity = knownCities.includes(upperInput);

            // If input is just "Pima" or "Pinal" (or "Pima County"), we don't want to send it as address/city
            const isCountyOnly = upperInput.includes('COUNTY') || upperInput === 'PIMA' || upperInput === 'PINAL';

            const payload = {
                state: 'AZ',
                county: county,
                city: isCity ? searchInput : '',
                zip_code: isZip ? searchInput : '',
                // If it's not a zip, not a known city, and not just a county name, treat it as an address fragment
                address: (!isZip && !isCity && !isCountyOnly) ? searchInput : '',
                distress_type: searchFilters.distress_type,
                property_types: searchFilters.property_types,
                limit: searchFilters.limit
            };

            console.log("DEBUG PAYLOAD:", payload);

            const res = await fetch('http://127.0.0.1:8000/scout/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error('Search failed');
            const data = await res.json();

            // Server now handles filtering, so we just set the data
            set({ scoutedLeads: data, activeZone: 'leads' });
        } catch (error) {
            console.error("Failed to fetch scouted leads:", error);
        }
    },

    filterDeals: (query: string) => {
        const { leads } = get();
        if (!query) {
            set({ filteredLeads: leads });
            return;
        }

        const lowerQuery = query.toLowerCase();
        const filtered = leads.filter(lead =>
            lead.address.toLowerCase().includes(lowerQuery) ||
            (lead.owner_name && lead.owner_name.toLowerCase().includes(lowerQuery)) ||
            (lead.parcel_id && lead.parcel_id.includes(lowerQuery))
        );
        set({ filteredLeads: filtered });
    }
}));
