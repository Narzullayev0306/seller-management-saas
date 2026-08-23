import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Geist, Geist_Mono } from "next/font/google";

import { AuthProvider } from "@/lib/auth";
import { CustomerAuthProvider } from "@/lib/customer-auth";
import { ThemeInitScript, ThemeProvider } from "@/lib/theme";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "Seller Management SaaS",
    template: "%s | Seller Management SaaS",
  },
  description:
    "Multi-tenant seller management platform: orders, inventory, products, customers and analytics with role-based access control.",
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#4f46e5",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <head>
        <ThemeInitScript />
      </head>
      <body className="min-h-full bg-slate-50 font-sans text-slate-900 dark:bg-slate-950 dark:text-slate-100">
        <ThemeProvider>
          <AuthProvider>
            <CustomerAuthProvider>{children}</CustomerAuthProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}