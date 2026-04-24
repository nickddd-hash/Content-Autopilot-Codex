"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Breadcrumbs() {
  const pathname = usePathname();
  const paths = pathname.split("/").filter(Boolean);

  if (paths.length === 0) return null;

  return (
    <nav className="breadcrumbs">
      <Link href="/">Дашборд</Link>
      {paths.map((path, index) => {
        const href = `/${paths.slice(0, index + 1).join("/")}`;
        const isLast = index === paths.length - 1;

        let label = path;
        if (path === "products") label = "Продукты";
        else if (path === "settings") label = "Настройки";
        else if (path === "content-plans") label = "Планы";
        else if (path === "items") label = "Темы";

        if (path.length > 20) label = "Детали";

        return (
          <span key={href}>
            <span className="separator">/</span>
            {isLast ? <span className="current">{label}</span> : <Link href={href}>{label}</Link>}
          </span>
        );
      })}
    </nav>
  );
}
