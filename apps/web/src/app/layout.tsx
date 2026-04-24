import "./globals.css";
import type { Metadata } from "next";
import { ReactNode } from "react";

import Breadcrumbs from "@/components/Breadcrumbs";
import Sidebar from "@/components/Sidebar";

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
