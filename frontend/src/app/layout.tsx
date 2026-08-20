import type { Metadata } from "next";
import Link from "next/link";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "SentiVest AI",
  description: "Turn financial noise into investment insights.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="border-b border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
            <Link href="/" className="text-lg font-semibold text-brand-600 dark:text-brand-500">
              SentiVest AI
            </Link>
            <nav className="flex gap-6 text-sm font-medium text-gray-500 dark:text-gray-400">
              <Link href="/" className="hover:text-gray-900 dark:hover:text-gray-100">
                Dashboard
              </Link>
              <Link href="/chat" className="hover:text-gray-900 dark:hover:text-gray-100">
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
