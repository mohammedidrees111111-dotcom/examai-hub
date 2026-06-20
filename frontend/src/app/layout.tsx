import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ExamAI Hub - Smart Learning Platform",
  description: "AI-powered exam prediction, teacher mode, summarization, flashcards, and study plans. Supports 20+ languages.",
  keywords: "AI exam prediction, study summarizer, teacher mode, flashcards, AI learning, exam preparation",
  robots: "index, follow",
  icons: { icon: "/favicon.svg", apple: "/logo.svg" },
  openGraph: {
    title: "ExamAI Hub - Smart Learning Platform",
    description: "AI-powered exam prediction, teacher mode, and summarization tools",
    type: "website",
    images: ["/logo.svg"],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const pubId = process.env.NEXT_PUBLIC_ADSENSE_PUB_ID;
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <head>
        {pubId && (
          <script
            async
            src={`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-${pubId}`}
            crossOrigin="anonymous"
          />
        )}
      </head>
      <body className="min-h-full flex flex-col">
        <AuthProvider>
            <Navbar />
            <main className="flex-1">{children}</main>
            <Footer />
        </AuthProvider>
      </body>
    </html>
  );
}
