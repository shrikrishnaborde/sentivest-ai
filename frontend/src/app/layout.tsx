import type { Metadata } from "next";
import Link from "next/link";
import { Logo } from "@/components/Logo";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "SentiVest AI",
  description: "Turn financial noise into investment insights.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="sticky top-0 z-50 border-b border-gray-200/80 bg-white/80 backdrop-blur-md dark:border-gray-800/80 dark:bg-gray-950/80">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3.5">
            <Link href="/" className="group flex items-center gap-2.5">
              <Logo className="h-8 w-8 shrink-0 transition-transform group-hover:scale-105" />
              <span className="flex items-baseline gap-1.5">
                <span className="bg-gradient-to-r from-brand-600 to-fuchsia-500 bg-clip-text text-lg font-bold tracking-tight text-transparent dark:from-brand-500 dark:to-fuchsia-400">
                  SentiVest
                </span>
                <span className="rounded-full bg-brand-50 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-brand-600 dark:bg-brand-500/10 dark:text-brand-400">
                  AI
                </span>
              </span>
            </Link>
            <nav className="flex gap-6 text-sm font-medium text-gray-500 dark:text-gray-400">
              <Link href="/" className="transition-colors hover:text-gray-900 dark:hover:text-gray-100">
                Dashboard
              </Link>
              <Link href="/chat" className="transition-colors hover:text-gray-900 dark:hover:text-gray-100">
                Ask SentiVest
              </Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-6 py-10">{children}</main>
      </body>
    </html>
  );
}
