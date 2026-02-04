import * as React from "react"
import { cn } from "@/lib/utils"

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, label, error, ...props }, ref) => {
    return (
      <div className="w-full space-y-2">
        {label && (
          <label className="text-sm font-bold uppercase tracking-wider text-black">
            {label}
          </label>
        )}
        <input
          type={type}
          className={cn(
            "flex h-12 w-full border-3 border-black bg-white px-4 py-3 text-base font-bold text-black ring-offset-white file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-500 focus-visible:outline-none focus-visible:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] disabled:cursor-not-allowed disabled:opacity-50",
            "rounded-none transition-all",
            error && "border-red-600 focus-visible:shadow-[4px_4px_0px_0px_rgba(220,38,38,1)]",
            className
          )}
          ref={ref}
          {...props}
        />
        {error && (
          <p className="text-sm font-bold text-red-600">{error}</p>
        )}
      </div>
    )
  }
)
Input.displayName = "Input"

export { Input }
