import React, { useState, useEffect, useRef } from 'react';
import { Search } from 'lucide-react';
import { useAppStore } from '@/lib/store';

interface AutocompleteProps {
    value: string;
    onChange: (value: string) => void;
    onSearch: () => void;
    placeholder?: string;
}

export default function AutocompleteInput({ value, onChange, onSearch, placeholder }: AutocompleteProps) {
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const wrapperRef = useRef<HTMLDivElement>(null);
    const { searchFilters } = useAppStore();

    useEffect(() => {
        // Close suggestions when clicking outside
        function handleClickOutside(event: MouseEvent) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    useEffect(() => {
        const fetchSuggestions = async () => {
            if (value.length < 3) {
                setSuggestions([]);
                return;
            }

            // Don't fetch if it looks like a zip or city (simple heuristic)
            if (/^\d{5}$/.test(value) || ['TUCSON', 'MARANA'].includes(value.toUpperCase())) {
                setSuggestions([]);
                return;
            }

            try {
                const res = await fetch(`http://localhost:8000/scout/autocomplete?query=${encodeURIComponent(value)}`);
                if (res.ok) {
                    const data = await res.json();
                    setSuggestions(data.suggestions || []);
                    setIsOpen(true);
                }
            } catch (error) {
                console.error("Failed to fetch suggestions:", error);
            }
        };

        const debounce = setTimeout(fetchSuggestions, 300);
        return () => clearTimeout(debounce);
    }, [value]);

    const handleSelect = (suggestion: string) => {
        onChange(suggestion);
        setIsOpen(false);
        // Optional: Trigger search immediately on selection? 
        // For now, let user hit enter or click search
    };

    return (
        <div ref={wrapperRef} className="relative w-full max-w-md">
            <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                    type="text"
                    placeholder={placeholder || "Search city, zip, or address..."}
                    className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white placeholder-gray-400 focus:outline-none focus:border-green-500 transition-colors"
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && onSearch()}
                />
            </div>

            {isOpen && suggestions.length > 0 && (
                <ul className="absolute z-50 w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    {suggestions.map((suggestion, index) => (
                        <li
                            key={index}
                            className="px-4 py-2 hover:bg-gray-700 cursor-pointer text-sm text-gray-200"
                            onClick={() => handleSelect(suggestion)}
                        >
                            {suggestion}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
