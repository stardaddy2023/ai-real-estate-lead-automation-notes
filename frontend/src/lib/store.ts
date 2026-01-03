import { create } from 'zustand';

interface Property {
    id: number;
    address: string;
    status: string;
    strategy: string;
    distress_score?: number;
    score?: number; // Keep for backward compatibility if needed
    reasoning?: string;
    owner_name?: string;
    mailing_address?: string;
    property_type?: string;
    beds?: number;
    baths?: number;
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

export interface ScoutResult {
    id: string;
    address: string;
    owner_name: string;
    mailing_address: string;
    property_type: string;
    last_sale_date?: string;
    last_sale_price?: number;
    assessed_value?: number;
    year_built?: number;
    sqft?: number;
    lot_size?: number;
    distress_signals: string[];
    distress_score: number;
    latitude: number;
    longitude: number;
    beds?: number;
    baths?: number;
    pool?: boolean;
    garage?: boolean;
    arv?: number;
    phone?: string;
    email?: string;
    parcel_id?: string;
    violation_count?: number;
    violations?: Array<{ description: string; activity_num: string }>;
}

interface AppState {
    selectedProperty: Property | null;
    isFilterOpen: boolean;
    isDetailPanelOpen: boolean;
    activeZone: 'market_scout' | 'leads' | 'my_leads' | 'deals' | 'crm' | 'contacts' | 'campaigns' | 'analytics' | 'settings';
    leads: Property[];
    filteredLeads: Property[];
    viewMode: 'map' | 'list';

    // Lead Scout State
    leadScout: {
        query: string;
        results: ScoutResult[];
        loading: boolean;
        selectedPropertyTypes: string[];
        selectedDistressTypes: string[];
        limit: number;
        minBeds: string;
        minBaths: string;
        minSqft: string;
        viewMode: 'map' | 'list';
        highlightedLeadId: string | null;
        panToLeadId: string | null;
        selectedLeadIds: Set<string>;
        bounds: { north: number, south: number, east: number, west: number } | null;
    };

    setSelectedProperty: (property: Property | null) => void;
    toggleFilter: () => void;
    toggleDetailPanel: (isOpen: boolean) => void;
    setActiveZone: (zone: AppState['activeZone']) => void;
    setViewMode: (mode: 'map' | 'list') => void;
    fetchLeads: () => Promise<void>;
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

    // Lead Scout Initial State
    leadScout: {
        query: "",
        results: [],
        loading: false,
        selectedPropertyTypes: [],
        selectedDistressTypes: [],
        limit: 100,
        minBeds: "",
        minBaths: "",
        minSqft: "",
        viewMode: 'map',
        highlightedLeadId: null,
        panToLeadId: null,
        selectedLeadIds: new Set(),
        bounds: null,
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
            selectedDistressTypes: [],
            limit: 100,
            minBeds: "",
            minBaths: "",
            minSqft: "",
            viewMode: 'map',
            highlightedLeadId: null,
            panToLeadId: null,
            selectedLeadIds: new Set(),
            bounds: null,
        }
    })),

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
