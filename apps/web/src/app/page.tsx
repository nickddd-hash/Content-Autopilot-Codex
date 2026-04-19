import Link from "next/link";
import { fetchJson, statusLabel } from "@/lib/api";

type DashboardSummary = {
  total_products: number;
  active_products: number;
  autopilot_enabled_products: number;
  total_content_plans: number;
  planned_items: number;
  published_items: number;
  failed_items: number;
  running_jobs: number;
};

type Product = {
  id: string;
  name: string;
  slug: string;
  category: string | null;
  lifecycle_stage: string | null;
  is_active: boolean;
  primary_channels: string[];
};

type BrandProfile = {
  brand_name: string | null;
  brand_summary: string | null;
  core_messages: string[];
  channel_strategy: Record<string, string>;
} | null;

type ContentPlan = {
  id: string;
  month: string;
  theme: string;
  status: string;
  items: Array<{ id: string; status: string; title: string }>;
};

function getBadgeClass(status: string) {
  const s = status.toLowerCase();
  if (["published", "completed", "active"].includes(s)) return "badge badge-success";
  if (["draft", "planned"].includes(s)) return "badge badge-outline";
  if (["failed", "error"].includes(s)) return "badge badge-danger";
  if (["running", "in_progress"].includes(s)) return "badge badge-warning";
  return "badge badge-info";
}

export default async function HomePage() {
  const [summary, products, brandProfile, contentPlans] = await Promise.all([
    fetchJson<DashboardSummary>("/dashboard/summary", {
      total_products: 0,
      active_products: 0,
      autopilot_enabled_products: 0,
      total_content_plans: 0,
      planned_items: 0,
      published_items: 0,
      failed_items: 0,
      running_jobs: 0,
    }),
    fetchJson<Product[]>("/products", []),
    fetchJson<BrandProfile>("/brand-profile", null),
    fetchJson<ContentPlan[]>("/content-plans", []),
  ]);

  const metrics = [
    { label: "Products", value: summary.total_products, hint: `${summary.active_products} active` },
    { label: "Autopilot", value: summary.autopilot_enabled_products, hint: "projects" },
    { label: "Plans", value: summary.total_content_plans, hint: `${summary.planned_items} topics in progress` },
    { label: "Jobs", value: summary.running_jobs, hint: `${summary.failed_items} failed` },
  ];

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">Athena Content OS</p>
          <h1>Dashboard</h1>
          <p className="lead">Overview of your brands, products, and content generation pipeline.</p>
        </div>
        <div style={{ display: "flex", gap: "12px" }}>
          <Link href="/settings" className="btn">Settings</Link>
          <Link href="/products/new" className="btn btn-primary">+ New product</Link>
        </div>
      </header>

      <section className="stats-grid">
        {metrics.map((metric) => (
          <article key={metric.label} className="stat-card">
            <span className="stat-label">{metric.label}</span>
            <strong className="stat-value">{metric.value}</strong>
            <p className="stat-hint">{metric.hint}</p>
          </article>
        ))}
      </section>

      <section className="panel-grid">
        <article className="panel">
          <div className="panel-header">
            <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
              <div style={{ background: "rgba(255,255,255,0.05)", padding: "10px", borderRadius: "12px" }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 16V7a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v9m16 0H4m16 0 1.28 2.55a1 1 0 0 1-.9 1.45H3.62a1 1 0 0 1-.9-1.45L4 16"></path></svg>
              </div>
              <div>
                <span className="panel-kicker">System</span>
                <h2 className="panel-title">Active products</h2>
              </div>
            </div>
            <span className="badge badge-accent">{products.length} total</span>
          </div>
          <div className="list-container">
            {products.length > 0 ? (
              products.map((product) => (
                <div key={product.id} className="list-item">
                  <div>
                    <Link href={`/products/${product.id}`} className="list-item-title item-link" style={{ textDecoration: "none" }}>
                      {product.name}
                    </Link>
                    <span className="list-item-sub">
                      {product.category || "General"} · {product.lifecycle_stage || "Launch"}
                    </span>
                  </div>
                  <div>
                    <span className={getBadgeClass(product.is_active ? "active" : "failed")}>
                      {product.is_active ? "Active" : "Disabled"}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <strong>No products yet</strong>
                <p>Add your first product to start content generation.</p>
              </div>
            )}
          </div>
        </article>

        <article className="panel">
          <div className="panel-header">
            <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
              <div style={{ background: "rgba(255,255,255,0.05)", padding: "10px", borderRadius: "12px" }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon></svg>
              </div>
              <div>
                <span className="panel-kicker">Strategy</span>
                <h2 className="panel-title">Brand profile</h2>
              </div>
            </div>
          </div>
          {brandProfile ? (
            <div className="key-value-stack">
              <div className="kv-pair">
                <span className="kv-label">Brand name</span>
                <span className="kv-val">{brandProfile.brand_name || "Untitled"}</span>
              </div>
              <div className="kv-pair">
                <span className="kv-label">Description</span>
                <span className="kv-val">{brandProfile.brand_summary || "Description is not filled in yet."}</span>
              </div>
              <div className="kv-pair">
                <span className="kv-label">Core messages</span>
                <span className="kv-val">
                  {brandProfile.core_messages.length > 0 ? brandProfile.core_messages.join(" • ") : "Not defined yet."}
                </span>
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <strong>Brand profile is missing</strong>
              <p>The autopilot needs a brand profile to understand voice and publishing rules.</p>
            </div>
          )}
        </article>

        <article className="panel panel-wide">
          <div className="panel-header">
            <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
              <div style={{ background: "rgba(255,255,255,0.05)", padding: "10px", borderRadius: "12px" }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
              </div>
              <div>
                <span className="panel-kicker">Execution</span>
                <h2 className="panel-title">Active content plans</h2>
              </div>
            </div>
          </div>
          <div className="list-container">
            {contentPlans.length > 0 ? (
              contentPlans.map((plan) => (
                <div key={plan.id} className="list-item">
                  <div style={{ minWidth: "300px" }}>
                    <span className="list-item-title">{plan.theme}</span>
                    <span className="list-item-sub">{plan.month}</span>
                  </div>
                  <div style={{ flex: 1, display: "flex", gap: "10px", flexWrap: "wrap", margin: "0 20px" }}>
                    {plan.items.slice(0, 3).map((item, i) => (
                      <Link key={item.id} href={`/content-plans/${plan.id}/items/${item.id}`} className="badge badge-outline" style={{ textDecoration: "none" }}>
                        {item.title || `Topic ${i + 1}`}
                      </Link>
                    ))}
                    {plan.items.length > 3 && <span className="badge badge-accent">+{plan.items.length - 3} more</span>}
                  </div>
                  <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
                    <span className={getBadgeClass(plan.status)}>{statusLabel(plan.status)}</span>
                    <Link href={`/content-plans/${plan.id}`} className="btn btn-sm">
                      Open plan
                    </Link>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <strong>No plans yet</strong>
                <p>Create a plan for the next month to start the workflow.</p>
              </div>
            )}
          </div>
        </article>
      </section>
    </>
  );
}