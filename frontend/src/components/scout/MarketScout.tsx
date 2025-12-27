"use client"

import { useState } from 'react';
import { Map, Construction, TrendingUp, Home, Users, Building } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { HeatmapView } from './HeatmapView';

interface MarketAnalysis {
    market_name: string;
    score: number;
    verdict: string;
    metrics: {
        unemployment_rate: number;
        building_permits: number;
        mortgage_rate: number;
        population_growth: number;
    };
    dates: {
        unemployment: string;
        building_permits: string;
        permits?: string;
        mortgage_rate: string;
        mortgage?: string;
        population_growth: string;
        population?: string;
    };
    breakdown: {
        unemployment_score: number;
        permit_score: number;
        rate_score: number;
        pop_score: number;
    };
}

export function MarketScout() {
    const [selectedMarket, setSelectedMarket] = useState('04019'); // Default Pima
    const [analysis, setAnalysis] = useState<MarketAnalysis | null>(null);
    const [loading, setLoading] = useState(false);

    const markets = [
        { id: '04019', name: 'Pima County, AZ', state: '04', county: '019' },
        { id: '04013', name: 'Maricopa County, AZ', state: '04', county: '013' },
        { id: '04021', name: 'Pinal County, AZ', state: '04', county: '021' },
        { id: '48453', name: 'Travis County, TX', state: '48', county: '453' },
    ];

    const handleAnalyze = async () => {
        setLoading(true);
        const market = markets.find(m => m.id === selectedMarket);
        if (!market) return;

        try {
            const res = await fetch('http://127.0.0.1:8000/scout/market', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    state_fips: market.state,
                    county_fips: market.county,
                    market_name: market.name
                })
            });
            const data = await res.json();
            setAnalysis(data);
        } catch (error) {
            console.error("Analysis failed:", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="h-full flex flex-col bg-background text-foreground overflow-y-auto">
            {/* Header */}
            <div className="p-6 border-b border-border bg-card/50">
                <h1 className="text-2xl font-bold tracking-tight flex items-center">
                    <Map className="w-6 h-6 mr-3 text-primary" />
                    Market Recon
                </h1>
                <p className="text-muted-foreground mt-1">
                    Analyze market trends and identify hot spots using real-time economic data.
                </p>
            </div>

            <div className="p-6 max-w-5xl mx-auto w-full space-y-8">
                <Tabs defaultValue="report" className="w-full">
                    <TabsList className="mb-6">
                        <TabsTrigger value="report">Market Report</TabsTrigger>
                        <TabsTrigger value="heatmap">Heatmap</TabsTrigger>
                    </TabsList>

                    <TabsContent value="report" className="space-y-8">
                        {/* Controls */}
                        <div className="flex items-center space-x-4 bg-card p-4 rounded-lg border border-border">
                            <select
                                className="flex-1 bg-background border border-border rounded-md px-3 py-2"
                                value={selectedMarket}
                                onChange={(e) => setSelectedMarket(e.target.value)}
                            >
                                {markets.map(m => (
                                    <option key={m.id} value={m.id}>{m.name}</option>
                                ))}
                            </select>
                            <button
                                onClick={handleAnalyze}
                                disabled={loading}
                                className="px-6 py-2 bg-primary text-black font-bold rounded-md hover:bg-primary/90 transition-all disabled:opacity-50"
                            >
                                {loading ? 'Analyzing...' : 'Analyze Market'}
                            </button>
                        </div>

                        {/* Results */}
                        {analysis && (
                            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                                {/* Score Card */}
                                <div className="p-8 rounded-xl border border-primary/20 bg-primary/5 text-center relative overflow-hidden">
                                    <div className="absolute inset-0 bg-grid-white/5 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.5))]" />
                                    <h2 className="text-3xl font-bold mb-2 relative z-10">{analysis.market_name}</h2>
                                    <div className="text-6xl font-black text-primary font-mono my-4 relative z-10">
                                        {analysis.score}/100
                                    </div>
                                    <div className="inline-block px-4 py-1 rounded-full bg-background/50 border border-primary/30 text-primary font-bold relative z-10">
                                        {analysis.verdict}
                                    </div>
                                </div>

                                {/* Metrics Grid */}
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                    <MetricCard
                                        icon={Users}
                                        label="Unemployment"
                                        value={`${analysis.metrics.unemployment_rate}%`}
                                        date={analysis.dates.unemployment}
                                        score={analysis.breakdown.unemployment_score}
                                        maxScore={25}
                                    />
                                    <MetricCard
                                        icon={Construction}
                                        label="Building Permits"
                                        value={analysis.metrics.building_permits.toLocaleString()}
                                        date={analysis.dates.building_permits || analysis.dates.permits} // Handle key mismatch if any
                                        score={analysis.breakdown.permit_score}
                                        maxScore={25}
                                    />
                                    <MetricCard
                                        icon={Home}
                                        label="Mortgage Rate"
                                        value={`${analysis.metrics.mortgage_rate}%`}
                                        date={analysis.dates.mortgage_rate || analysis.dates.mortgage}
                                        score={analysis.breakdown.rate_score}
                                        maxScore={10}
                                    />
                                    <MetricCard
                                        icon={TrendingUp}
                                        label="Pop. Growth"
                                        value={`${analysis.metrics.population_growth}%`}
                                        date={analysis.dates.population_growth || analysis.dates.population}
                                        score={analysis.breakdown.pop_score}
                                        maxScore={40}
                                    />
                                </div>
                            </div>
                        )}

                        {!analysis && !loading && (
                            <div className="text-center py-20 text-muted-foreground">
                                <Building className="w-16 h-16 mx-auto mb-4 opacity-20" />
                                <p>Select a market and click analyze to see real-time data.</p>
                            </div>
                        )}
                    </TabsContent>

                    <TabsContent value="heatmap">
                        <HeatmapView />
                    </TabsContent>
                </Tabs>
            </div>
        </div>
    );
}

function MetricCard({ icon: Icon, label, value, date, score, maxScore }: any) {
    return (
        <div className="p-4 rounded-lg border border-border bg-card hover:border-primary/50 transition-colors">
            <div className="flex items-center justify-between mb-2">
                <Icon className="w-5 h-5 text-muted-foreground" />
                <span className="text-xs font-mono text-primary">+{score}/{maxScore} pts</span>
            </div>
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="text-2xl font-bold font-mono">{value}</p>
            <p className="text-xs text-muted-foreground mt-1">Source: {date}</p>
        </div>
    );
}
