"use client";

import { MapPin, Home, TrendingUp, AlertCircle } from 'lucide-react';

interface LeadListProps {
    leads: any[];
    onSelect: (lead: any) => void;
}

export function LeadList({ leads, onSelect }: LeadListProps) {
    if (!leads || leads.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                <Home className="w-12 h-12 mb-4 opacity-20" />
                <p>No leads found.</p>
            </div>
        );
    }

    return (
        <div className="h-full overflow-y-auto p-6 bg-background/50 backdrop-blur-sm">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-7xl mx-auto">
                {leads.map((lead) => (
                    <div
                        key={lead.id}
                        onClick={() => onSelect(lead)}
                        className="group bg-card border border-border hover:border-primary/50 rounded-lg p-4 cursor-pointer transition-all hover:shadow-lg hover:shadow-primary/5 relative overflow-hidden"
                    >
                        {/* Status Badge */}
                        <div className="absolute top-4 right-4">
                            <span className={`text-[10px] font-bold px-2 py-1 rounded-full uppercase tracking-wider ${lead.distress_score > 80 ? 'bg-red-500/20 text-red-500' :
                                lead.distress_score > 50 ? 'bg-yellow-500/20 text-yellow-500' :
                                    'bg-green-500/20 text-green-500'
                                }`}>
                                Score: {lead.distress_score}
                            </span>
                        </div>

                        <div className="flex items-start space-x-3 mb-3">
                            <div className="p-2 bg-muted rounded-md group-hover:bg-primary/10 group-hover:text-primary transition-colors">
                                <Home className="w-5 h-5" />
                            </div>
                            <div>
                                <h3 className="font-bold text-sm line-clamp-1 pr-16">{lead.address}</h3>
                                <p className="text-xs text-muted-foreground">{lead.city || 'Tucson'}, {lead.state || 'AZ'} {lead.zip_code}</p>
                                {lead.parcel_id && (
                                    <p className="text-[10px] text-muted-foreground mt-0.5 font-mono">APN: {lead.parcel_id}</p>
                                )}
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground mt-4 pt-4 border-t border-border/50">
                            <div className="flex items-center">
                                <TrendingUp className="w-3 h-3 mr-1.5" />
                                <span>{lead.strategy || 'Wholesale'}</span>
                            </div>
                            <div className="flex items-center justify-end">
                                <span className={lead.status === 'New' ? 'text-blue-400' : ''}>{lead.status}</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
