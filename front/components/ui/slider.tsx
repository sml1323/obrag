"use client"

import * as React from "react"
import * as SliderPrimitive from "@radix-ui/react-slider"

import { cn } from "@/lib/utils"

interface SliderProps extends React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root> {
  value: number[]
  onValueChange: (value: number[]) => void
  label?: string
}

const Slider = React.forwardRef<
  React.ElementRef<typeof SliderPrimitive.Root>,
  SliderProps
>(({ className, value, onValueChange, label, ...props }, ref) => {
  const currentValue = value[0] || 0
  
  const getThumbColor = (val: number) => {
    if (val <= 33) return "bg-[#f87171]"
    if (val <= 66) return "bg-[#fde047]"
    return "bg-[#a3e635]"
  }

  return (
    <div className="w-full space-y-2">
      {label && (
        <div className="flex justify-between items-center text-sm font-bold">
          <span>{label}</span>
          <span>{currentValue}%</span>
        </div>
      )}
      <SliderPrimitive.Root
        ref={ref}
        className={cn(
          "relative flex w-full touch-none select-none items-center",
          className
        )}
        value={value}
        onValueChange={onValueChange}
        {...props}
      >
        <SliderPrimitive.Track className="relative h-[8px] w-full grow overflow-hidden bg-[#1a1a1a]">
          <SliderPrimitive.Range className="absolute h-full bg-transparent" />
        </SliderPrimitive.Track>
        <SliderPrimitive.Thumb
          className={cn(
            "block h-6 w-6 border-[3px] border-black transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
            getThumbColor(currentValue),
            "rounded-none"
          )}
        />
      </SliderPrimitive.Root>
    </div>
  )
})
Slider.displayName = SliderPrimitive.Root.displayName

export { Slider }
