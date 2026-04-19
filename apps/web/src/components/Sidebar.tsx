import SidebarLink from "./SidebarLink";
import { fetchJson } from "@/lib/api";

type SidebarProduct = {
  id: string;
  name: string;
  slug: string;
};

export default async function Sidebar() {
  const products = await fetchJson<SidebarProduct[]>("/products", []);

  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-dot" /> 
        <SidebarLink href="/">Athena Content</SidebarLink>
      </div>
      
      <nav className="nav-links">
        <SidebarLink href="/" className="nav-link">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="9" rx="1"></rect><rect x="14" y="3" width="7" height="5" rx="1"></rect><rect x="14" y="12" width="7" height="9" rx="1"></rect><rect x="3" y="16" width="7" height="5" rx="1"></rect></svg>
          Дашборд
        </SidebarLink>
        
        <div className="nav-section">
          <span className="nav-section-title">Продукты</span>
          {products.map(product => (
            <SidebarLink 
              key={product.id} 
              href={`/products/${product.id}`} 
              className="nav-link nav-link-sub"
            >
              {product.name}
            </SidebarLink>
          ))}
          {products.length === 0 && (
            <span className="nav-link-empty">Нет продуктов</span>
          )}
        </div>

        <div className="nav-section">
          <span className="nav-section-title">Система</span>
          <SidebarLink href="/settings" className="nav-link">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path><circle cx="12" cy="12" r="3"></circle></svg>
            Настройки API
          </SidebarLink>
        </div>
      </nav>
    </aside>
  );
}
