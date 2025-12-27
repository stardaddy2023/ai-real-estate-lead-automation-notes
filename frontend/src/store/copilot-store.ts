import { create } from 'zustand'

export interface Message {
    id: string
    role: 'user' | 'assistant' | 'system'
    content: string
    timestamp: number
}

export interface CoPilotContext {
    type: 'lead' | 'market' | 'global'
    data: any
}

interface CoPilotState {
    isOpen: boolean
    messages: Message[]
    context: CoPilotContext | null

    toggle: () => void
    setOpen: (open: boolean) => void
    addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void
    setContext: (context: CoPilotContext) => void
}

export const useCoPilotStore = create<CoPilotState>((set) => ({
    isOpen: false, // Default closed
    messages: [
        {
            id: 'welcome',
            role: 'assistant',
            content: "I'm online. How can I assist you with your real estate operations today?",
            timestamp: Date.now()
        }
    ],
    context: null,

    toggle: () => set((state) => ({ isOpen: !state.isOpen })),
    setOpen: (open) => set({ isOpen: open }),

    addMessage: (msg) => set((state) => ({
        messages: [...state.messages, {
            ...msg,
            id: Math.random().toString(36).substring(7),
            timestamp: Date.now()
        }]
    })),

    setContext: (context) => set({ context })
}))
