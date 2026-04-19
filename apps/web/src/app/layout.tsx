import "./globals.css";
import type { Metadata } from "next";
import { ReactNode } from "react";
import Sidebar from "@/components/Sidebar";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "Content Autopilot",
  description: "Personal AI marketing autopilot",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <div className="app-shell">
          <Sidebar />
          <main className="main-content">
            <Breadcrumbs />
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}

