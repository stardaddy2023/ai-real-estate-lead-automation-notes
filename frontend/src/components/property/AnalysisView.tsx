"use client";

import { useState } from 'react';
import { ChevronDown, ChevronUp, FileText, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AnalysisViewProps {
    analysis: string;
}

export function AnalysisView({ analysis }: AnalysisViewProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const [openSections, setOpenSections] = useState<Record<string, boolean>>({});

    if (!analysis) return null;

    // Simple parsing logic: Split by lines that look like headers (starting with **)
    // This is a heuristic based on the Gemini output format seen in the screenshot
    const parseSections = (text: string) => {
        const lines = text.split('\n');
        const sections: { title: string; content: string[] }[] = [];
        let currentSection = { title: 'Summary', content: [] as string[] };

        lines.forEach(line => {
            const trimmed = line.trim();
            // Check for bold headers like "**Header**" or "**Header:**"
            if (trimmed.startsWith('**') && trimmed.length < 100 && (trimmed.endsWith('**') || trimmed.includes('**:'))) {
                // Push previous section
                if (currentSection.content.length > 0) {
                    sections.push(currentSection);
                }
                // Start new section
                // Remove asterisks for clean title
                const title = trimmed.replace(/\*\*/g, '').replace(':', '').trim();
                currentSection = { title, content: [] };
            } else {
                if (trimmed) currentSection.content.push(trimmed);
            }
        });

        // Push last section
        if (currentSection.content.length > 0) {
            sections.push(currentSection);
        }

        return sections;
    };

    const sections = parseSections(analysis);
    const summarySection = sections[0]; // Assume first section is summary/intro
    const detailSections = sections.slice(1);

    const toggleSection = (title: string) => {
        setOpenSections(prev => ({
            ...prev,
            [title]: !prev[title]
        }));
    };

    return (
        <div className="mt-4 space-y-3">
            {/* Summary Card */}
            <div className="p-4 bg-background/50 rounded-lg border border-primary/20 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-primary/50" />
                <h4 className="text-xs font-bold text-primary uppercase tracking-wider mb-2 flex items-center">
                    <Sparkles className="w-3 h-3 mr-2" />
                    {summarySection.title}
                </h4>
                <div className="text-xs text-muted-foreground font-mono leading-relaxed space-y-2">
                    {summarySection.content.map((line, i) => (
                        <p key={i}>{line}</p>
                    ))}
                </div>

                {!isExpanded && detailSections.length > 0 && (
                    <button
                        onClick={() => setIsExpanded(true)}
                        className="mt-3 text-xs text-primary font-bold hover:underline flex items-center"
                    >
                        View Full Analysis <ChevronDown className="w-3 h-3 ml-1" />
                    </button>
                )}
            </div>

            {/* Expanded Details */}
            {isExpanded && (
                <div className="space-y-2 animate-in fade-in slide-in-from-top-2 duration-300">
                    {detailSections.map((section, idx) => (
                        <div key={idx} className="border border-border rounded-md bg-card/30 overflow-hidden">
                            <button
                                onClick={() => toggleSection(section.title)}
                                className="w-full flex items-center justify-between p-3 text-left hover:bg-muted/50 transition-colors"
                            >
                                <span className="text-xs font-bold text-foreground">{section.title}</span>
                                {openSections[section.title] ? (
                                    <ChevronUp className="w-3 h-3 text-muted-foreground" />
                                ) : (
                                    <ChevronDown className="w-3 h-3 text-muted-foreground" />
                                )}
                            </button>

                            {openSections[section.title] && (
                                <div className="p-3 pt-0 text-xs text-muted-foreground font-mono leading-relaxed border-t border-border/50 bg-background/50">
                                    {section.content.map((line, i) => (
                                        <p key={i} className="mb-1 last:mb-0">{line}</p>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))}

                    <button
                        onClick={() => setIsExpanded(false)}
                        className="w-full py-2 text-xs text-muted-foreground hover:text-foreground flex items-center justify-center border-t border-transparent hover:border-border transition-all"
                    >
                        <ChevronUp className="w-3 h-3 mr-1" /> Show Less
                    </button>
                </div>
            )}
        </div>
    );
}
