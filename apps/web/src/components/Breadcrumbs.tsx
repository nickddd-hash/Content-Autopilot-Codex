"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type BreadcrumbItem = {
  href?: string;
  label: string;
};

function buildBreadcrumbItems(pathname: string): BreadcrumbItem[] {
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length === 0) return [];

  const [section, firstId, nestedSection, nestedId] = segments;

  if (section === "archive") {
    return [{ href: "/archive", label: "Архив" }];
  }

  if (section === "settings") {
    return [{ href: "/settings", label: "Настройки" }];
  }

  if (section === "products") {
    if (firstId === "new") {
      return [{ href: "/products/new", label: "Новый продукт" }];
    }
    return [{ href: firstId ? `/products/${firstId}` : undefined, label: "Продукт" }];
  }

  if (section === "content-plans") {
    const items: BreadcrumbItem[] = [];
    if (firstId) {
      items.push({ href: `/content-plans/${firstId}`, label: "Контент-план" });
    } else {
      items.push({ label: "Контент-планы" });
    }

    if (nestedSection === "items" && nestedId && firstId) {
      items.push({ href: `/content-plans/${firstId}/items/${nestedId}`, label: "Тема" });
    }

    return items;
  }

  return [{ label: section }];
}

export default function Breadcrumbs() {
  const pathname = usePathname();
  const items = buildBreadcrumbItems(pathname);

  if (items.length === 0) return null;

  return (
    <nav className="breadcrumbs" aria-label="Хлебные крошки">
      <Link href="/">Дашборд</Link>
      {items.map((item, index) => {
        const isLast = index === items.length - 1;

        return (
          <span key={`${item.href || item.label}-${index}`}>
            <span className="separator">/</span>
            {item.href && !isLast ? <Link href={item.href}>{item.label}</Link> : <span className="current">{item.label}</span>}
          </span>
        );
      })}
    </nav>
  );
}
