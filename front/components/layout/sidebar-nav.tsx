"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navItems = [
  { href: '/chat', label: 'CHAT', icon: '💬' },
  { href: '/para', label: 'PROJECTS', icon: '📁' },
  { href: '/embedding', label: 'EMBED', icon: '🧠' },
  { href: '/settings', label: 'CONFIG', icon: '⚙️' },
];

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <nav className="flex flex-col gap-4 w-full p-4">
      {navItems.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`
              flex items-center gap-3 px-4 py-3 
              text-sm font-bold tracking-wider
              border-[3px] border-[#1a1a1a] 
              transition-all duration-150 ease-in-out
              ${isActive 
                ? 'bg-[#FF6B35] text-[#1a1a1a] translate-x-[-2px] translate-y-[-2px] shadow-[4px_4px_0px_#1a1a1a]' 
                : 'bg-[#FFFEF0] text-[#1a1a1a] hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[4px_4px_0px_#1a1a1a]'
              }
            `}
          >
            <span className="text-xl">{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
