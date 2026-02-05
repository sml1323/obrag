"use client";

import React from 'react';
import { SidebarNav } from "./sidebar-nav";
import Mascot, { MascotProvider } from "./mascot";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <MascotProvider>
      <div className="flex h-screen w-screen bg-[#FFFEF0] text-[#1a1a1a] overflow-hidden font-sans">
        <aside className="w-[240px] flex-shrink-0 flex flex-col border-r-[3px] border-[#1a1a1a] bg-[#FFFEF0] h-full">
            <div className="p-6 border-b-[3px] border-[#1a1a1a] flex items-center justify-center bg-[#FF6B35]">
                <h1 className="text-3xl font-black tracking-tighter italic">OBRAG</h1>
            </div>
            
            <div className="flex-1 py-6 overflow-y-auto">
                <SidebarNav />
            </div>

            <div className="p-4 border-t-[3px] border-[#1a1a1a] flex flex-col items-center justify-center gap-2 bg-[#FFFEF0]">
                 <div className="text-xs font-bold uppercase tracking-widest mb-2">System Status</div>
                 <Mascot />
            </div>
        </aside>

        <main className="flex-1 h-full overflow-hidden relative flex flex-col">
           <header className="h-16 border-b-[3px] border-[#1a1a1a] flex items-center px-6 justify-between bg-[#FFFEF0]">
              <div className="font-bold text-lg">/ WORKSPACE</div>
              <div className="text-sm font-mono opacity-60">v1.0.0-alpha</div>
           </header>

           <div className="flex-1 overflow-auto p-8">
              {children}
           </div>
        </main>
      </div>
    </MascotProvider>
  );
}
