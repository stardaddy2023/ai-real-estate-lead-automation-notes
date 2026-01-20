import { create } from 'zustand';

export interface Property {
    id: string;
    address: string;
    price: number;
    sqft: number;
    beds: number;
    baths: number;
    year_built: number;
    arv: number;
    rehab_cost: number;
    images: string[];
    description: string;
    status: 'New' | 'Contacted' | 'Offer Sent' | 'Under Contract' | 'Closed';
    coordinates: { lat: number; lng: number };
}

export interface ScoutResult {
    id: string;
    address: string;
    latitude: number;
    longitude: number;
    owner_name?: string;
    mailing_address?: string;
    property_type?: string;
    assessed_value?: number;
    arv?: number;
    sqft?: number;
    beds?: number;
    baths?: number;
    year_built?: number;
    distress_signals: string[];
    violation_count?: number;
    violation_description?: string;
    parcel_id?: string;
    zoning?: string;
    lot_size?: number;
    estimated_value?: number;
    last_sold_date?: string;
    last_sold_price?: number;
    property_url?: string;
    primary_photo?: string;
    flood_zone?: string;
    school_district?: string;
    tax_status?: string;
    tax_link?: string;
}

export interface AppState {
    selectedProperty: Property | null;
    isFilterOpen: boolean;
    isDetailPanelOpen: boolean;
    activeZone: 'market_scout' | 'lead_inbox' | 'offer_generator' | 'dispositions';
    leads: any[];
    filteredLeads: any[];
    viewMode: 'map' | 'list';
    googleMapsApiKey: string | null;

    // Lead Scout State
    leadScout: {
        query: string;
        results: ScoutResult[];
        loading: boolean;
        selectedPropertyTypes: string[];
        selectedPropertySubTypes: string[];  // Parcel use codes for sub-types
        selectedDistressTypes: string[];
        limit: number;
        minBeds: string;
        maxBeds: string;
        minBaths: string;
        maxBaths: string;
        minSqft: string;
        maxSqft: string;
        minYearBuilt: string;
        maxYearBuilt: string;
        selectedHotList: string[];
        selectedStatuses: string[];
        // Property feature filters
        hasPool: boolean | null;
        hasGarage: boolean | null;
        hasGuestHouse: boolean | null;
        viewMode: 'map' | 'list';
        highlightedLeadId: string | null;
        panToLeadId: string | null;
        selectedLeadIds: Set<string>;
        bounds: { north: number, south: number, east: number, west: number } | null;
        error: string | null;
        lastViewedLeadId: string | null;
    };

    setSelectedProperty: (property: Property | null) => void;
    toggleFilter: () => void;
    toggleDetailPanel: (isOpen: boolean) => void;
    setActiveZone: (zone: AppState['activeZone']) => void;
    setViewMode: (mode: 'map' | 'list') => void;
    fetchLeads: () => Promise<void>;
    fetchConfig: () => Promise<void>;
    filterDeals: (query: string) => void;

    // Lead Scout Actions
    setLeadScoutState: (state: Partial<AppState['leadScout']>) => void;
    resetLeadScoutState: () => void;

    // Scout State (Legacy/MarketRecon?)
    searchFilters: {
        zip_code: string;
        county: string;
        distress_type: string[];
        property_types: string[];
        limit: number;
    };
    setSearchFilters: (filters: Partial<AppState['searchFilters']>) => void;
    scoutedLeads: any[];
}

export const useAppStore = create<AppState>((set, get) => ({
    selectedProperty: null,
    isFilterOpen: false,
    isDetailPanelOpen: false,
    activeZone: 'market_scout',
    leads: [],
    filteredLeads: [],
    viewMode: 'map',
    googleMapsApiKey: null,

    // Lead Scout Initial State
    leadScout: {
        query: "",
        results: [],
        loading: false,
        selectedPropertyTypes: [],
        selectedPropertySubTypes: [],  // Parcel use codes for sub-types
        selectedDistressTypes: [],
        limit: 100,
        minBeds: "",
        maxBeds: "",
        minBaths: "",
        maxBaths: "",
        minSqft: "",
        maxSqft: "",
        minYearBuilt: "",
        maxYearBuilt: "",
        selectedHotList: [],
        selectedStatuses: [],
        // Property feature filters
        hasPool: null,
        hasGarage: null,
        hasGuestHouse: null,
        viewMode: 'map',
        highlightedLeadId: null,
        panToLeadId: null,
        selectedLeadIds: new Set(),
        bounds: null,
        error: null,
        lastViewedLeadId: null,
    },

    // Scout State (Legacy)
    searchFilters: {
        zip_code: '',
        county: 'Pima', // Default to Pima
        distress_type: ['all'],
        property_types: ['Single Family'],
        limit: 100
    },
    scoutedLeads: [],

    setSelectedProperty: (property) => set({ selectedProperty: property, isDetailPanelOpen: !!property }),
    toggleFilter: () => set((state) => ({ isFilterOpen: !state.isFilterOpen })),
    toggleDetailPanel: (isOpen) => set({ isDetailPanelOpen: isOpen }),
    setActiveZone: (zone) => set({ activeZone: zone }),
    setViewMode: (mode) => set({ viewMode: mode }),

    setLeadScoutState: (newState) => set((state) => ({
        leadScout: { ...state.leadScout, ...newState }
    })),

    resetLeadScoutState: () => set((state) => ({
        leadScout: {
            query: "",
            results: [],
            loading: false,
            selectedPropertyTypes: [],
            selectedPropertySubTypes: [],
            selectedDistressTypes: [],
            limit: 100,
            minBeds: "",
            maxBeds: "",
            minBaths: "",
            maxBaths: "",
            minSqft: "",
            maxSqft: "",
            minYearBuilt: "",
            maxYearBuilt: "",
            selectedHotList: [],
            selectedStatuses: [],
            // Property feature filters
            hasPool: null,
            hasGarage: null,
            hasGuestHouse: null,
            viewMode: 'map',
            highlightedLeadId: null,
            panToLeadId: null,
            selectedLeadIds: new Set(),
            bounds: null,
            error: null,
            lastViewedLeadId: null,
        }
    })),

    setSearchFilters: (filters) => set((state) => ({
        searchFilters: { ...state.searchFilters, ...filters }
    })),

    fetchLeads: async () => {
        try {
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
            const res = await fetch(`${baseUrl}/api/v1/leads`);
            const data = await res.json();
            set({ leads: data, filteredLeads: data }); // Initialize filteredLeads with all leads
        } catch (error) {
            console.error("Failed to fetch leads:", error);
            set((state) => ({
                leadScout: { ...state.leadScout, error: error instanceof Error ? error.message : "Unknown error" }
            }));
        }
    },

    fetchConfig: async () => {
        try {
            // In development, we might need the full URL if not proxied
            // In production (Cloud Run), relative path should work if served from same origin or configured correctly
            // For now assuming backend is at same host or proxied, or we use env var for base URL
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
            const res = await fetch(`${baseUrl}/api/v1/settings/public-config`);
            if (!res.ok) throw new Error('Failed to fetch config');
            const data = await res.json();
            set({ googleMapsApiKey: data.googleMapsApiKey });
        } catch (error) {
            console.error("Failed to fetch config:", error);
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
