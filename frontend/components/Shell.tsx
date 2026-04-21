import Link from "next/link";
import type { ReactNode } from "react";

import { ChartBarIcon, HomeIcon, Squares2X2Icon, UserCircleIcon } from "@heroicons/react/24/outline";

const nav = [
  { href: "/", label: "Overview", icon: HomeIcon },
  { href: "/facilities", label: "Facilities", icon: Squares2X2Icon },
  { href: "/admin", label: "Admin", icon: ChartBarIcon },
  { href: "/admin/login", label: "Login", icon: UserCircleIcon }
];

export function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
          <Link href="/" className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-lg bg-ink text-sm font-bold text-white">SS</span>
            <div>
              <p className="text-base font-semibold text-ink">Smart Seat Analytics</p>
              <p className="text-xs text-slate-500">Facility congestion intelligence</p>
            </div>
          </Link>
          <nav className="flex flex-wrap gap-2">
            {nav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="focus-ring inline-flex items-center gap-2 rounded-lg border border-transparent px-3 py-2 text-sm font-medium text-slate-600 hover:border-line hover:bg-panel"
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}

