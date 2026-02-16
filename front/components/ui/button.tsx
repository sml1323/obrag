import * as React from "react"
import { cn } from "@/lib/utils"

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  isLoading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "default", isLoading, children, disabled, ...props }, ref) => {
    const variants = {
      primary: "bg-[#FF6B35] text-white hover:bg-[#ff8f6b] border-3 border-black shadow-[4px_4px_0px_0px_#1a1a1a] hover:-translate-y-0.5 hover:translate-x-0.5 hover:shadow-[6px_6px_0px_0px_#1a1a1a] active:translate-x-0.5 active:translate-y-0.5 active:shadow-[2px_2px_0px_0px_#1a1a1a]",
      secondary: "bg-[#4ECDC4] text-black hover:bg-[#7edcd6] border-3 border-black shadow-[4px_4px_0px_0px_#1a1a1a] hover:-translate-y-0.5 hover:translate-x-0.5 hover:shadow-[6px_6px_0px_0px_#1a1a1a] active:translate-x-0.5 active:translate-y-0.5 active:shadow-[2px_2px_0px_0px_#1a1a1a]",
      danger: "bg-[#FF4444] text-white hover:bg-[#ff7b7b] border-3 border-black shadow-[4px_4px_0px_0px_#1a1a1a] hover:-translate-y-0.5 hover:translate-x-0.5 hover:shadow-[6px_6px_0px_0px_#1a1a1a] active:translate-x-0.5 active:translate-y-0.5 active:shadow-[2px_2px_0px_0px_#1a1a1a]",
      ghost: "bg-transparent hover:bg-accent hover:text-accent-foreground border-0 shadow-none",
      outline: "bg-transparent border border-input hover:bg-accent hover:text-accent-foreground shadow-none",
    }

    const sizes = {
      default: "h-12 px-8 text-base",
      sm: "h-8 px-3 text-sm",
      lg: "h-14 px-10 text-lg",
      icon: "h-10 w-10 p-0",
    }

    return (
      <button
        className={cn(
          "inline-flex items-center justify-center font-bold uppercase tracking-wider transition-all",
          "disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none",
          variants[variant],
          sizes[size],
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
