"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';

export type MascotState = 'idle' | 'loading' | 'speaking';

interface MascotContextType {
  mascotState: MascotState;
  setMascotState: (state: MascotState) => void;
}

const MascotContext = createContext<MascotContextType | undefined>(undefined);

export function useMascot() {
  const context = useContext(MascotContext);
  if (!context) {
    throw new Error('useMascot must be used within a MascotProvider');
  }
  return context;
}

export function MascotProvider({ children }: { children: ReactNode }) {
  const [mascotState, setMascotState] = useState<MascotState>('idle');
  return (
    <MascotContext.Provider value={{ mascotState, setMascotState }}>
      {children}
    </MascotContext.Provider>
  );
}

interface MascotProps {
  state?: MascotState;
}

export default function Mascot({ state: propState }: MascotProps) {
  const context = useContext(MascotContext);
  const currentState = propState || context?.mascotState || 'idle';
  
  const [svgContent, setSvgContent] = useState<string>('');
  
  useEffect(() => {
    const fileName = 
      currentState === 'loading' ? 'loading.svg' :
      currentState === 'speaking' ? 'speak.svg' : 
      'default.svg';
      
    const path = `/character/${fileName}`;

    fetch(path)
      .then(res => res.text())
      .then(text => {
        setSvgContent(text);
      })
      .catch(err => console.error("Failed to load mascot SVG", err));
  }, [currentState]);

  return (
    <div 
      className="w-[200px] h-[200px] bg-[#FFFEF0] border-[3px] border-[#1a1a1a] shadow-[4px_4px_0px_#1a1a1a] flex items-center justify-center overflow-hidden p-4"
      dangerouslySetInnerHTML={{ __html: svgContent }}
    />
  );
}
