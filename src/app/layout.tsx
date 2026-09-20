import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Geist, Geist_Mono } from "next/font/google";
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
  metadataBase: new URL('https://jailmap.com'),
  title: {
    default: 'JailMap — Public records, clearer context',
    template: '%s | JailMap',
  },
  description: 'JailMap aggregates official booking records from every US state into one searchable platform. Free search, source-linked records, transparent corrections.',
  openGraph: {
    type: 'website',
    siteName: 'JailMap',
    title: 'JailMap — Public records, clearer context',
    description: 'Official booking records from every US state, searchable in one place.',
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
