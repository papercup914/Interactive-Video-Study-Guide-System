import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Nanum_Pen_Script } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import { ThemeToggle } from "@/components/ThemeToggle";
import { TaskProvider } from "@/app/contexts/TaskContext";
import { TaskWidget } from "@/components/TaskWidget";
import { LearnerProfileWidget } from "@/components/LearnerProfileWidget";
import { AuthStatusWidget } from "@/components/AuthStatusWidget";
import { Providers } from "./providers";

const inter = Inter({
  variable: "--font-geist-sans", // Keeping variable name for compatibility
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

const jbMono = JetBrains_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const nanumPen = Nanum_Pen_Script({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-handwriting",
});

export const metadata: Metadata = {
  title: "Interactive Video Study Guide System",
  description: "AI-powered study guides from your favorite videos",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body
        className={`${inter.variable} ${jbMono.variable} ${nanumPen.variable} antialiased min-h-screen flex flex-col`}
      >
        <Providers>
          <TaskProvider>
            <header className="border-b border-border-subtle bg-surface/80 backdrop-blur-md sticky top-0 z-50">
              <div className="max-w-[120rem] mx-auto px-4 h-16 flex items-center justify-between">
                <Link href="/" className="font-extrabold text-xl flex items-center gap-2 tracking-tight hover:opacity-90 transition-opacity">
                  <span className="text-foreground">StudyGuide</span>
                  <span className="text-muted-foreground">.AI</span>
                </Link>
                <div className="flex items-center gap-2">
                  <LearnerProfileWidget />
                  <ThemeToggle />
                  <AuthStatusWidget />
                </div>
              </div>
            </header>
            <main className="flex-1 w-full flex flex-col">
              {children}
            </main>
            <TaskWidget />
          </TaskProvider>
        </Providers>
      </body>
    </html>
  );
}
