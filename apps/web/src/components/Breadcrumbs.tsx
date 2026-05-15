"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const SEGMENT_LABELS: Record<string, string> = {
  products: "Продукты",
  settings: "Настройки",
  "content-plans": "Планы",
  items: "Темы",
  archive: "Архив",
  "new-plan": "Новый план",
};

// Routes that have no own page — redirect to nearest valid ancestor
const DEAD_ROUTES: Record<string, string> = {
  "/content-plans": "/",
  "/products": "/",
};

export default function Breadcrumbs() {
  const pathname = usePathname();
  const paths = pathname.split("/").filter(Boolean);

  if (paths.length === 0) return null;

  return (
    <nav className="breadcrumbs">
      <Link href="/">Дашборд</Link>
      {paths.map((path, index) => {
        const naturalHref = `/${paths.slice(0, index + 1).join("/")}`;
        const isLast = index === paths.length - 1;

        let label = SEGMENT_LABELS[path] ?? path;
        if (path.length > 20) label = "Детали";

        // /content-plans/[planId]/items has no page — link to the plan instead
        let href = DEAD_ROUTES[naturalHref] ?? naturalHref;
        if (path === "items" && index >= 2) {
          href = `/${paths.slice(0, index).join("/")}`;
        }

        return (
          <span key={naturalHref}>
            <span className="separator">/</span>
            {isLast ? <span className="current">{label}</span> : <Link href={href}>{label}</Link>}
          </span>
        );
      })}
    </nav>
  );
}
