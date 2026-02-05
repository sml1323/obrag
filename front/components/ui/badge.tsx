import * as React from "react"
import { cn } from "@/lib/utils"

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger';
}

export function Badge({ 
  className, 
  variant = 'default', 
  ...props 
}: BadgeProps) {
  const variants = {
    default: "bg-gray-200 text-black",
    success: "bg-[#a3e635] text-black", // Lime green
    warning: "bg-[#fde047] text-black", // Yellow
    danger: "bg-[#f87171] text-black",   // Red
  }

  return (
    <div 
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 text-xs font-bold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        "border-2 border-black", // 2px border
        "rounded-none",          // No border radius
        variants[variant],
        className
      )} 
      {...props} 
    />
  )
}
