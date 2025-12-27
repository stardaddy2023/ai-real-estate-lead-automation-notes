import * as React from "react"
import { ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"

const Accordion = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement> & { type?: "single" | "multiple"; collapsible?: boolean }
>(({ className, ...props }, ref) => (
    <div ref={ref} className={cn("w-full", className)} {...props} />
))
Accordion.displayName = "Accordion"

const AccordionItem = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement> & { value: string }
>(({ className, ...props }, ref) => (
    <div ref={ref} className={cn("border-b", className)} {...props} />
))
AccordionItem.displayName = "AccordionItem"

const AccordionTrigger = React.forwardRef<
    HTMLButtonElement,
    React.ButtonHTMLAttributes<HTMLButtonElement>
>(({ className, children, ...props }, ref) => {
    // Note: This is a simplified version that doesn't use Context for open state.
    // It relies on the parent or self-management if we were fully implementing Radix.
    // BUT, for this specific task, I'll make it a simple controlled component or just use a local state wrapper if I can.
    // Actually, implementing the full Context API is a bit much for a quick fix.
    // Let's just make a simple "SimpleAccordion" that works for our use case.
    return (
        <button
            ref={ref}
            className={cn(
                "flex flex-1 items-center justify-between py-4 font-medium transition-all hover:underline [&[data-state=open]>svg]:rotate-180",
                className
            )}
            {...props}
        >
            {children}
            <ChevronDown className="h-4 w-4 shrink-0 transition-transform duration-200" />
        </button>
    )
})
AccordionTrigger.displayName = "AccordionTrigger"

const AccordionContent = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement>
>(({ className, children, ...props }, ref) => (
    <div
        ref={ref}
        className={cn(
            "overflow-hidden text-sm transition-all data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down",
            className
        )}
        {...props}
    >
        <div className={cn("pb-4 pt-0", className)}>{children}</div>
    </div>
))
AccordionContent.displayName = "AccordionContent"

// Simple Context-based implementation for "Single" mode
interface AccordionContextType {
    value: string | undefined;
    onValueChange: (value: string) => void;
}
const AccordionContext = React.createContext<AccordionContextType>({ value: undefined, onValueChange: () => { } });

export function SimpleAccordion({ children, className, ...props }: { children: React.ReactNode, className?: string }) {
    const [value, setValue] = React.useState<string>("");

    return (
        <AccordionContext.Provider value={{ value, onValueChange: (v) => setValue(v === value ? "" : v) }}>
            <div className={cn("w-full", className)} {...props}>
                {children}
            </div>
        </AccordionContext.Provider>
    )
}

export function SimpleAccordionItem({ value, children, className }: { value: string, children: React.ReactNode, className?: string }) {
    return (
        <div className={cn("border-b", className)}>
            {React.Children.map(children, child => {
                if (React.isValidElement(child)) {
                    return React.cloneElement(child as React.ReactElement<any>, { value });
                }
                return child;
            })}
        </div>
    )
}

export function SimpleAccordionTrigger({ children, className, value }: { children: React.ReactNode, className?: string, value?: string }) {
    const { value: selectedValue, onValueChange } = React.useContext(AccordionContext);
    const isOpen = selectedValue === value;

    return (
        <button
            onClick={() => value && onValueChange(value)}
            className={cn(
                "flex flex-1 items-center justify-between py-4 font-medium transition-all hover:underline",
                className
            )}
        >
            {children}
            <ChevronDown className={cn("h-4 w-4 shrink-0 transition-transform duration-200", isOpen ? "rotate-180" : "")} />
        </button>
    )
}

export function SimpleAccordionContent({ children, className, value }: { children: React.ReactNode, className?: string, value?: string }) {
    const { value: selectedValue } = React.useContext(AccordionContext);
    const isOpen = selectedValue === value;

    if (!isOpen) return null;

    return (
        <div className={cn("overflow-hidden text-sm pb-4 pt-0", className)}>
            {children}
        </div>
    )
}
