"use client";

import { useState, useEffect, useRef } from 'react';
import { X, Plus, Loader2 } from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { useMapsLibrary } from '@vis.gl/react-google-maps';

export function AddLeadDialog({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
    const { setSelectedProperty } = useAppStore();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const placesLib = useMapsLibrary('places');
    const addressInputRef = useRef<HTMLInputElement>(null);

    const [formData, setFormData] = useState({
        address: '',
        owner_name: '',
        phone: '',
        email: '',
        status: 'New',
        strategy: 'Wholesale',
        sqft: '',
        bedrooms: '',
        bathrooms: '',
        year_built: '',
        lot_size: '',
        has_pool: 'No',
        has_garage: 'No',
        has_guesthouse: 'No',
        latitude: null as number | null,
        longitude: null as number | null
    });

    useEffect(() => {
        if (!placesLib || !addressInputRef.current) return;

        const autocomplete = new placesLib.Autocomplete(addressInputRef.current, {
            fields: ['formatted_address', 'geometry', 'address_components'],
            types: ['address'],
        });

        autocomplete.addListener('place_changed', () => {
            const place = autocomplete.getPlace();

            if (place.formatted_address) {
                setFormData(prev => ({
                    ...prev,
                    address: place.formatted_address || '',
                    latitude: place.geometry?.location?.lat() || null,
                    longitude: place.geometry?.location?.lng() || null,
                }));
            }
        });
    }, [placesLib, isOpen]);

    if (!isOpen) return null;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            // Prepare payload - convert numbers
            const payload = {
                ...formData,
                sqft: formData.sqft ? parseInt(formData.sqft) : null,
                bedrooms: formData.bedrooms ? parseInt(formData.bedrooms) : null,
                bathrooms: formData.bathrooms ? parseFloat(formData.bathrooms) : null,
                year_built: formData.year_built ? parseInt(formData.year_built) : null,
                lot_size: formData.lot_size ? parseFloat(formData.lot_size) : null,
                distress_score: 50, // Default for manual entry
            };

            const res = await fetch('http://localhost:8000/leads', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                throw new Error(`Failed to create lead: ${res.statusText}`);
            }

            const newLead = await res.json();

            // Select the new lead to open it immediately
            setSelectedProperty(newLead);

            // Close modal
            onClose();

            // Optional: Refresh list (handled by Dashboard usually, but we might need to trigger a re-fetch if the list is static)
            // For now, opening it is good feedback.
            window.location.reload(); // Simple way to refresh the map/list for now

        } catch (err: any) {
            console.error("Error creating lead:", err);
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-sm">
            <div className="w-full max-w-2xl bg-background border border-border rounded-lg shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-card/50">
                    <h2 className="text-lg font-bold tracking-tight flex items-center">
                        <Plus className="w-5 h-5 mr-2 text-primary" />
                        Add New Lead
                    </h2>
                    <button onClick={onClose} className="p-2 hover:bg-muted rounded-full transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
                    {error && (
                        <div className="p-3 bg-red-500/10 border border-red-500/50 text-red-500 text-sm rounded">
                            {error}
                        </div>
                    )}

                    {/* Section: Basic Info */}
                    <div className="space-y-4">
                        <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider border-b border-border pb-1">
                            Property Information
                        </h3>
                        <div className="grid grid-cols-1 gap-4">
                            <div>
                                <label className="text-xs font-medium mb-1 block">Address *</label>
                                <input
                                    required
                                    ref={addressInputRef}
                                    name="address"
                                    value={formData.address}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 bg-muted/50 border border-border rounded focus:outline-none focus:border-primary font-mono text-sm"
                                    placeholder="Start typing address..."
                                />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="text-xs font-medium mb-1 block">Status</label>
                                <select
                                    name="status"
                                    value={formData.status}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 bg-muted/50 border border-border rounded focus:outline-none focus:border-primary text-sm"
                                >
                                    <option value="New">New</option>
                                    <option value="Analyzing">Analyzing</option>
                                    <option value="Offer Sent">Offer Sent</option>
                                    <option value="Under Contract">Under Contract</option>
                                </select>
                            </div>
                            <div>
                                <label className="text-xs font-medium mb-1 block">Strategy</label>
                                <select
                                    name="strategy"
                                    value={formData.strategy}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 bg-muted/50 border border-border rounded focus:outline-none focus:border-primary text-sm"
                                >
                                    <option value="Wholesale">Wholesale</option>
                                    <option value="Fix and Flip">Fix and Flip</option>
                                    <option value="Buy and Hold">Buy and Hold</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    {/* Section: Owner Info */}
                    <div className="space-y-4">
                        <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider border-b border-border pb-1">
                            Owner Details
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="text-xs font-medium mb-1 block">Owner Name</label>
                                <input
                                    name="owner_name"
                                    value={formData.owner_name}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 bg-muted/50 border border-border rounded focus:outline-none focus:border-primary text-sm"
                                    placeholder="John Doe"
                                />
                            </div>
                            <div>
                                <label className="text-xs font-medium mb-1 block">Phone</label>
                                <input
                                    name="phone"
                                    value={formData.phone}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 bg-muted/50 border border-border rounded focus:outline-none focus:border-primary font-mono text-sm"
                                    placeholder="(555) 123-4567"
                                />
                            </div>
                            <div className="col-span-2">
                                <label className="text-xs font-medium mb-1 block">Email</label>
                                <input
                                    name="email"
                                    type="email"
                                    value={formData.email}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 bg-muted/50 border border-border rounded focus:outline-none focus:border-primary font-mono text-sm"
                                    placeholder="owner@example.com"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Section: Property Specs */}
                    <div className="space-y-4">
                        <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider border-b border-border pb-1">
                            Property Specs
                        </h3>
                        <div className="grid grid-cols-3 gap-4">
                            <div>
                                <label className="text-xs font-medium mb-1 block">Sqft</label>
                                <input
                                    name="sqft"
                                    type="number"
                                    value={formData.sqft}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 bg-muted/50 border border-border rounded focus:outline-none focus:border-primary font-mono text-sm"
                                    placeholder="1500"
                                />
                            </div>
                            <div>
                                <label className="text-xs font-medium mb-1 block">Beds</label>
                                <input
                                    name="bedrooms"
                                    type="number"
                                    value={formData.bedrooms}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 bg-muted/50 border border-border rounded focus:outline-none focus:border-primary font-mono text-sm"
                                    placeholder="3"
                                />
                            </div>
                            <div>
                                <label className="text-xs font-medium mb-1 block">Baths</label>
                                <input
                                    name="bathrooms"
                                    type="number"
                                    step="0.5"
                                    value={formData.bathrooms}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 bg-muted/50 border border-border rounded focus:outline-none focus:border-primary font-mono text-sm"
                                    placeholder="2"
                                />
                            </div>
                            <div>
                                <label className="text-xs font-medium mb-1 block">Year Built</label>
                                <input
                                    name="year_built"
                                    type="number"
                                    value={formData.year_built}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 bg-muted/50 border border-border rounded focus:outline-none focus:border-primary font-mono text-sm"
                                    placeholder="1980"
                                />
                            </div>
                            <div>
                                <label className="text-xs font-medium mb-1 block">Lot Size (Acres)</label>
                                <input
                                    name="lot_size"
                                    type="number"
                                    step="0.01"
                                    value={formData.lot_size}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 bg-muted/50 border border-border rounded focus:outline-none focus:border-primary font-mono text-sm"
                                    placeholder="0.25"
                                />
                            </div>
                        </div>
                        <div className="grid grid-cols-3 gap-4 pt-2">
                            <div>
                                <label className="text-xs font-medium mb-1 block">Pool</label>
                                <select
                                    name="has_pool"
                                    value={formData.has_pool}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 bg-muted/50 border border-border rounded focus:outline-none focus:border-primary text-sm"
                                >
                                    <option value="No">No</option>
                                    <option value="Yes">Yes</option>
                                </select>
                            </div>
                            <div>
                                <label className="text-xs font-medium mb-1 block">Garage</label>
                                <select
                                    name="has_garage"
                                    value={formData.has_garage}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 bg-muted/50 border border-border rounded focus:outline-none focus:border-primary text-sm"
                                >
                                    <option value="No">No</option>
                                    <option value="Yes">Yes</option>
                                </select>
                            </div>
                            <div>
                                <label className="text-xs font-medium mb-1 block">Guest House</label>
                                <select
                                    name="has_guesthouse"
                                    value={formData.has_guesthouse}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 bg-muted/50 border border-border rounded focus:outline-none focus:border-primary text-sm"
                                >
                                    <option value="No">No</option>
                                    <option value="Yes">Yes</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </form>

                {/* Footer */}
                <div className="p-4 border-t border-border bg-card/50 flex justify-end space-x-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={isLoading}
                        className="px-6 py-2 bg-primary text-black font-bold rounded-md hover:bg-primary/90 transition-all disabled:opacity-50 flex items-center"
                    >
                        {isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                        {isLoading ? 'Creating...' : 'Create Lead'}
                    </button>
                </div>
            </div>
        </div>
    );
}
