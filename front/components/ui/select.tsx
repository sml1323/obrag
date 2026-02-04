import * as React from "react"
import { cn } from "@/lib/utils"

export interface SelectProps
  extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: { value: string; label: string }[];
  error?: string;
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, options, error, ...props }, ref) => {
    return (
      <div className="w-full space-y-2">
        {label && (
          <label className="text-sm font-bold uppercase tracking-wider text-black">
            {label}
          </label>
        )}
        <div className="relative">
          <select
            className={cn(
              "flex h-12 w-full appearance-none border-3 border-black bg-white px-4 py-3 pr-8 text-base font-bold text-black ring-offset-white focus-visible:outline-none focus-visible:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] disabled:cursor-not-allowed disabled:opacity-50",
              "rounded-none transition-all",
              error && "border-red-600 focus-visible:shadow-[4px_4px_0px_0px_rgba(220,38,38,1)]",
              className
            )}
            ref={ref}
            {...props}
          >
            {options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <div className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2">
            <svg
              width="12"
              height="12"
              viewBox="0 0 12 12"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M1 3L6 8L11 3"
                stroke="black"
                strokeWidth="3"
                strokeLinecap="square"
              />
            </svg>
          </div>
        </div>
        {error && (
          <p className="text-sm font-bold text-red-600">{error}</p>
        )}
      </div>
    )
  }
)
Select.displayName = "Select"

export { Select }
