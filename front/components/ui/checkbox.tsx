"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface CheckboxProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  indeterminate?: boolean;
  className?: string;
}

export function Checkbox({ checked, onChange, label, indeterminate, className }: CheckboxProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div
        className={cn(
          "w-6 h-6 border-3 border-black cursor-pointer transition-all flex items-center justify-center bg-white hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]",
          checked || indeterminate ? "bg-[#FF6B35]" : "bg-white"
        )}
        onClick={() => onChange(!checked)}
      >
        {checked && !indeterminate && (
          <span className="text-black font-bold text-lg leading-none">✓</span>
        )}
        {indeterminate && (
          <span className="text-black font-bold text-lg leading-none">-</span>
        )}
      </div>
      {label && (
        <span 
          className="font-medium text-black cursor-pointer select-none"
          onClick={() => onChange(!checked)}
        >
          {label}
        </span>
      )}
    </div>
  );
}
