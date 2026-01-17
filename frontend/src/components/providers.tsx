"use client"

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useState } from "react"

import { Toaster } from "@/components/ui/toaster"

import { useAppStore } from "@/lib/store"

export function Providers({ children }: { children: React.ReactNode }) {
    const [queryClient] = useState(() => new QueryClient())
    const { fetchConfig } = useAppStore()

    // Fetch config on mount
    if (typeof window !== 'undefined') {
        // Simple effect-like behavior in render for now, or use useEffect
        // But since this is a client component, useEffect is better
    }

    // Actually let's use useEffect properly
    useState(() => {
        // This runs once on init
        useAppStore.getState().fetchConfig()
    })

    return (
        <QueryClientProvider client={queryClient}>
            {children}
            <Toaster />
        </QueryClientProvider>
    )
}
