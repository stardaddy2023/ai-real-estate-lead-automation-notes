"use client";

import { useAppStore } from '@/lib/store';
import { X, Home, Activity, DollarSign, FileText, Bot } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useState, useEffect } from 'react';
import { AnalysisView } from './AnalysisView';

export function PropertyPanel() {
    const { selectedProperty: _selectedProperty, isDetailPanelOpen, toggleDetailPanel, setSelectedProperty, setViewMode, setActiveZone } = useAppStore();
    const selectedProperty = _selectedProperty as any;
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isSkipTracing, setIsSkipTracing] = useState(false);
    const [isGeneratingOffer, setIsGeneratingOffer] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Fetch fresh data when panel opens or ID changes
    useEffect(() => {
        setError(null); // Always clear error when selection changes

        // Only fetch if ID is a number (existing lead in DB)
        // Scouted leads have address string as ID or no ID
        if (selectedProperty?.id && typeof selectedProperty.id === 'number') {
            fetch(`http://localhost:8000/leads/${selectedProperty.id}`)
                .then(res => {
                    if (!res.ok) throw new Error(`Failed to fetch lead: ${res.statusText}`);
                    return res.json();
                })
                .then(data => {
                    // Only update if data is actually different to avoid loop
                    // But for now, just relying on ID dependency should be enough
                    setSelectedProperty(data);
                })
                .catch(err => {
                    console.error("Error fetching lead details:", err);
                    setError(err.message);
                });
        }
    }, [selectedProperty?.id, setSelectedProperty]);

    if (!isDetailPanelOpen || !selectedProperty) return null;

    const handleRunComps = async () => {
        setIsAnalyzing(true);
        try {
            const res = await fetch(`http://localhost:8000/leads/${selectedProperty.id}/analyze`, {
                method: 'POST'
            });
            if (!res.ok) throw new Error('Analysis failed');
            const updatedLead = await res.json();
            setSelectedProperty(updatedLead);
        } catch (error: any) {
            console.error("Analysis error:", error);
            setError(error.message || "An error occurred during analysis");
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleSkipTrace = async () => {
        setIsSkipTracing(true);
        try {
            const res = await fetch(`http://localhost:8000/leads/${selectedProperty.id}/skiptrace`, {
                method: 'POST'
            });
            if (!res.ok) throw new Error('Skip trace failed');
            const updatedLead = await res.json();
            setSelectedProperty(updatedLead);
        } catch (error) {
            console.error("Skip trace error:", error);
        } finally {
            setIsSkipTracing(false);
        }
    };

    const handleGenerateOffer = async () => {
        setIsGeneratingOffer(true);
        setError(null);
        try {
            const res = await fetch(`http://localhost:8000/leads/${selectedProperty.id}/offer`, {
                method: 'POST'
            });
            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}));
                throw new Error(errorData.detail || `Offer generation failed: ${res.statusText}`);
            }
            const updatedLead = await res.json();
            setSelectedProperty(updatedLead);
        } catch (err: any) {
            console.error("Offer generation error:", err);
            setError(err.message);
        } finally {
            setIsGeneratingOffer(false);
        }
    };

    const isSavedLead = typeof selectedProperty.id === 'number';

    return (
        <div className="fixed inset-y-0 right-0 w-full md:w-[450px] bg-background/95 backdrop-blur-xl border-l border-border shadow-2xl z-50 transform transition-transform duration-300 ease-in-out flex flex-col">
            {/* Header */}
            <div className="h-16 border-b border-border flex items-center justify-between px-6 bg-card/50">
                <div>
                    <h2 className="font-bold text-lg tracking-tight">Property Details</h2>
                    <p className="text-xs text-muted-foreground font-mono">ID: {isSavedLead ? selectedProperty.id : 'SCOUTED'}</p>
                </div>
                <button
                    onClick={() => toggleDetailPanel(false)}
                    className="p-2 hover:bg-muted rounded-full transition-colors"
                >
                    <X className="w-5 h-5" />
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-8">
                {/* Error Alert */}
                {error && (
                    <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/50 text-red-500 text-sm font-mono">
                        ERROR: {error}
                    </div>
                )}

                {/* Main Info */}
                <div>
                    <h1 className="text-2xl font-bold leading-tight font-mono">{selectedProperty.address}</h1>
                    <div className="flex items-center mt-4 space-x-2">
                        <Badge variant="outline" className="border-primary/50 text-primary bg-primary/10">
                            {selectedProperty.status}
                        </Badge>
                        <Badge variant="secondary">
                            {selectedProperty.strategy}
                        </Badge>
                    </div>
                    {/* Contact Info */}
                    {(selectedProperty.phone || selectedProperty.email || selectedProperty.owner_name) && (
                        <div className="mt-4 p-3 bg-muted/30 rounded-lg border border-border space-y-2">
                            {selectedProperty.owner_name && (
                                <div className="flex items-start text-sm">
                                    <span className="text-muted-foreground w-20 shrink-0">Owner:</span>
                                    <span className="font-medium text-foreground">{selectedProperty.owner_name}</span>
                                </div>
                            )}
                            {selectedProperty.mailing_address && (
                                <div className="flex items-start text-sm">
                                    <span className="text-muted-foreground w-20 shrink-0">Mailing:</span>
                                    <span className="font-mono text-foreground text-xs">{selectedProperty.mailing_address}</span>
                                </div>
                            )}
                            {selectedProperty.phone && (
                                <div className="flex items-center text-sm">
                                    <span className="text-muted-foreground w-20 shrink-0">Phone:</span>
                                    <span className="font-mono text-foreground">{selectedProperty.phone}</span>
                                </div>
                            )}
                            {selectedProperty.email && (
                                <div className="flex items-center text-sm">
                                    <span className="text-muted-foreground w-20 shrink-0">Email:</span>
                                    <span className="font-mono text-foreground">{selectedProperty.email}</span>
                                </div>
                            )}
                            {selectedProperty.social_ids && (
                                <div className="flex items-center pt-2 space-x-3 border-t border-border/50 mt-2">
                                    {selectedProperty.social_ids.linkedin && (
                                        <a href={selectedProperty.social_ids.linkedin} target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-[#0077b5] transition-colors">
                                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" /></svg>
                                        </a>
                                    )}
                                    {selectedProperty.social_ids.facebook && (
                                        <a href={selectedProperty.social_ids.facebook} target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-[#1877f2] transition-colors">
                                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M9 8h-3v4h3v12h5v-12h3.642l.358-4h-4v-1.667c0-.955.192-1.333 1.115-1.333h2.885v-5h-3.808c-3.596 0-5.192 1.583-5.192 4.615v3.385z" /></svg>
                                        </a>
                                    )}
                                    {selectedProperty.social_ids.twitter && (
                                        <a href={selectedProperty.social_ids.twitter} target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-[#1da1f2] transition-colors">
                                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z" /></svg>
                                        </a>
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Property Data */}
                <div className="space-y-4">
                    <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider border-b border-border pb-2">
                        Property Data
                    </h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <InfoRow label="APN" value={selectedProperty.parcel_id || 'N/A'} />
                        <InfoRow label="Living Area" value={selectedProperty.sqft ? `${selectedProperty.sqft.toLocaleString()} sqft` : 'N/A'} />
                        <InfoRow label="Lot Size" value={selectedProperty.lot_size ? `${selectedProperty.lot_size} acres` : 'N/A'} />
                        <InfoRow label="Year Built" value={selectedProperty.year_built ? selectedProperty.year_built.toString() : 'N/A'} />
                        <InfoRow label="Bed/Bath" value={selectedProperty.bedrooms && selectedProperty.bathrooms ? `${selectedProperty.bedrooms} bd / ${selectedProperty.bathrooms} ba` : 'N/A'} />
                        <InfoRow label="Pool" value={selectedProperty.has_pool || 'No'} />
                        <InfoRow label="Garage" value={selectedProperty.has_garage || 'No'} />
                        <InfoRow label="Guest House" value={selectedProperty.has_guesthouse || 'No'} />
                        <InfoRow label="Last Sale" value={selectedProperty.last_sale_date || 'N/A'} />
                        <InfoRow label="Sale Price" value={selectedProperty.last_sale_price ? `$${selectedProperty.last_sale_price.toLocaleString()}` : 'N/A'} />
                    </div>
                </div>

                {/* AI Analysis Card */}
                <div className="p-4 rounded-lg border border-primary/20 bg-primary/5 relative overflow-hidden group">
                    <div className="absolute inset-0 bg-grid-white/5 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))]" />
                    <div className="relative z-10">
                        <div className="flex items-center justify-between mb-2">
                            <h3 className="text-sm font-bold text-primary flex items-center">
                                <Bot className={`w-4 h-4 mr-2 ${isAnalyzing ? 'animate-spin' : ''}`} />
                                {isAnalyzing ? 'ANALYZING...' : 'AI ANALYSIS'}
                            </h3>
                            <span className="text-xs font-mono text-primary/70">CONFIDENCE: 92%</span>
                        </div>
                        <div className="flex items-end justify-between">
                            <div>
                                <p className="text-xs text-muted-foreground uppercase tracking-wider">Distress Score</p>
                                <p className="text-4xl font-bold text-foreground font-mono">{selectedProperty.distress_score || selectedProperty.score}</p>
                            </div>
                            <div className="text-right">
                                <p className="text-xs text-muted-foreground uppercase tracking-wider">Est. Equity</p>
                                <p className="text-xl font-bold text-foreground font-mono">$142,000</p>
                            </div>
                        </div>
                        <div className="mt-4 h-1.5 w-full bg-background rounded-full overflow-hidden">
                            <div
                                className="h-full bg-primary shadow-[0_0_10px_#00ff80] transition-all duration-1000"
                                style={{ width: `${selectedProperty.distress_score || selectedProperty.score}%` }}
                            />
                        </div>
                        {selectedProperty.reasoning && (
                            <AnalysisView analysis={selectedProperty.reasoning} />
                        )}
                    </div>
                </div>

                {/* Actions Grid */}
                <div className="grid grid-cols-2 gap-3">
                    {isSavedLead ? (
                        <>
                            <ActionButton
                                icon={Activity}
                                label="Run Comps"
                                onClick={handleRunComps}
                                disabled={isAnalyzing}
                            />
                            <ActionButton
                                icon={DollarSign}
                                label={isSkipTracing ? "Tracing..." : "Skip Trace"}
                                onClick={handleSkipTrace}
                                disabled={isSkipTracing}
                            />
                            <ActionButton
                                icon={Home}
                                label="View on Maps"
                                onClick={() => {
                                    setActiveZone('deals' as any);
                                    setViewMode('map');
                                }}
                            />
                        </>
                    ) : (
                        <div className="col-span-2">
                            <button
                                className="w-full py-3 bg-green-500 text-black font-bold rounded-md hover:bg-green-400 transition-all flex items-center justify-center"
                                onClick={async () => {
                                    // Import single lead
                                    try {
                                        const res = await fetch('http://localhost:8000/scout/import', {
                                            method: 'POST',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify([selectedProperty])
                                        });
                                        if (res.ok) {
                                            // Refresh leads and maybe switch to deals view or update UI
                                            const { fetchLeads } = useAppStore.getState();
                                            await fetchLeads();
                                            // Close panel or show success
                                            toggleDetailPanel(false);
                                        }
                                    } catch (e) {
                                        console.error("Import failed", e);
                                    }
                                }}
                            >
                                <Bot className="w-5 h-5 mr-2" />
                                Import to Pipeline
                            </button>
                            <p className="text-xs text-center text-muted-foreground mt-2">
                                Import this lead to run comps, skip trace, and generate offers.
                            </p>
                        </div>
                    )}
                </div>



                {/* Debug View */}
                <div className="mt-8 p-4 bg-black/50 rounded border border-white/10">
                    <details>
                        <summary className="text-xs font-mono text-muted-foreground cursor-pointer hover:text-white">DEBUG: Raw Data</summary>
                        <pre className="mt-2 text-[10px] text-green-400 font-mono overflow-auto max-h-40">
                            {JSON.stringify(selectedProperty, null, 2)}
                        </pre>
                    </details>
                </div>
            </div>

            {/* Footer Actions */}
            <div className="p-4 border-t border-border bg-card/50">
                <button className="w-full py-3 bg-primary text-black font-bold rounded-md hover:bg-primary/90 transition-all shadow-[0_0_20px_rgba(0,255,128,0.2)] hover:shadow-[0_0_30px_rgba(0,255,128,0.4)] uppercase tracking-wide">
                    Start Campaign
                </button>
            </div>
        </div >
    );
}

function Badge({ children, variant = "default", className }: { children: React.ReactNode, variant?: "default" | "secondary" | "outline", className?: string }) {
    return (
        <span className={cn(
            "px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide",
            variant === "default" && "bg-primary text-primary-foreground",
            variant === "secondary" && "bg-secondary text-secondary-foreground",
            variant === "outline" && "border border-border text-foreground",
            className
        )}>
            {children}
        </span>
    );
}

interface ActionButtonProps {
    icon: any;
    label: string;
    onClick?: () => void;
    disabled?: boolean;
}

function ActionButton({ icon: Icon, label, onClick, disabled }: ActionButtonProps) {
    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className="flex flex-col items-center justify-center p-4 rounded-lg border border-border bg-card hover:bg-muted/50 hover:border-primary/50 transition-all group disabled:opacity-50 disabled:cursor-not-allowed"
        >
            <Icon className="w-5 h-5 mb-2 text-muted-foreground group-hover:text-primary transition-colors" />
            <span className="text-xs font-medium text-muted-foreground group-hover:text-foreground">{label}</span>
        </button>
    );
}

function InfoRow({ label, value }: { label: string, value: string }) {
    return (
        <div className="flex justify-between">
            <span className="text-muted-foreground">{label}</span>
            <span className="font-medium font-mono">{value}</span>
        </div>
    );
}
