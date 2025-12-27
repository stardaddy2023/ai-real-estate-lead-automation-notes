"use client"

import { useState, useRef, useEffect } from "react"
import { X, Send, Bot, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useCoPilotStore } from "@/store/copilot-store"
import { cn } from "@/lib/utils"

export function CoPilotSidebar() {
    const { isOpen, toggle, messages, addMessage, context } = useCoPilotStore()
    const [input, setInput] = useState("")
    const scrollRef = useRef<HTMLDivElement>(null)

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: "smooth" })
        }
    }, [messages, isOpen])

    const handleSend = () => {
        if (!input.trim()) return

        // Add User Message
        addMessage({ role: 'user', content: input })
        setInput("")

        // Mock AI Response (for now)
        setTimeout(() => {
            addMessage({
                role: 'assistant',
                content: "I'm analyzing that request. (AI Integration coming in Phase 4)"
            })
        }, 1000)
    }

    if (!isOpen) return null

    return (
        <div className="fixed right-0 top-0 h-screen w-[400px] bg-background/80 backdrop-blur-xl border-l border-border shadow-2xl z-50 flex flex-col transition-all duration-300">
            {/* Header */}
            <div className="p-4 border-b border-border flex items-center justify-between bg-background/50">
                <div className="flex items-center gap-2">
                    <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
                        <Bot className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                        <h3 className="font-bold text-sm">ARELA Co-Pilot</h3>
                        <div className="flex items-center gap-1.5">
                            <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                            <span className="text-xs text-muted-foreground">Systems Online</span>
                        </div>
                    </div>
                </div>
                <Button variant="ghost" size="icon" onClick={toggle}>
                    <X className="h-4 w-4" />
                </Button>
            </div>

            {/* Context Panel (if active) */}
            {context && (
                <div className="px-4 py-2 bg-muted/30 border-b border-border flex items-center gap-2 text-xs text-muted-foreground">
                    <Sparkles className="h-3 w-3 text-yellow-500" />
                    <span>Context: {context.type.toUpperCase()} - {JSON.stringify(context.data).substring(0, 30)}...</span>
                </div>
            )}

            {/* Chat Area */}
            <ScrollArea className="flex-1 p-4">
                <div className="space-y-4">
                    {messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={cn(
                                "flex w-max max-w-[80%] flex-col gap-2 rounded-lg px-3 py-2 text-sm",
                                msg.role === "user"
                                    ? "ml-auto bg-primary text-primary-foreground"
                                    : "bg-muted"
                            )}
                        >
                            {msg.content}
                        </div>
                    ))}
                    <div ref={scrollRef} />
                </div>
            </ScrollArea>

            {/* Input Area */}
            <div className="p-4 border-t border-border bg-background/50">
                <form
                    onSubmit={(e) => {
                        e.preventDefault()
                        handleSend()
                    }}
                    className="flex gap-2"
                >
                    <Input
                        placeholder="Ask Co-Pilot..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        className="flex-1 bg-background/50"
                    />
                    <Button type="submit" size="icon" disabled={!input.trim()}>
                        <Send className="h-4 w-4" />
                    </Button>
                </form>
            </div>
        </div>
    )
}
