import * as React from "react"
import { cn } from "@/lib/utils"

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  isLoading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", isLoading, children, disabled, ...props }, ref) => {
    const variants = {
      primary: "bg-[#FF6B35] text-white hover:bg-[#ff8f6b]",
      secondary: "bg-[#4ECDC4] text-black hover:bg-[#7edcd6]",
      danger: "bg-[#FF4444] text-white hover:bg-[#ff7b7b]",
    }

    return (
      <button
        className={cn(
          "inline-flex h-12 items-center justify-center border-3 border-black px-8 text-base font-bold uppercase tracking-wider transition-all",
          "shadow-[4px_4px_0px_0px_#1a1a1a]",
          "hover:-translate-y-0.5 hover:translate-x-0.5 hover:shadow-[6px_6px_0px_0px_#1a1a1a]",
          "active:translate-x-0.5 active:translate-y-0.5 active:shadow-[2px_2px_0px_0px_#1a1a1a]",
          "disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none",
          variants[variant],
          className
        )}
        ref={ref}
        disabled={isLoading || disabled}
        {...props}
      >
        {isLoading ? (
          <span className="flex items-center gap-1">
            LOADING
            <span className="animate-bounce">.</span>
            <span className="animate-bounce delay-100">.</span>
            <span className="animate-bounce delay-200">.</span>
          </span>
        ) : (
          children
        )}
      </button>
    )
  }
)
Button.displayName = "Button"

export { Button }
