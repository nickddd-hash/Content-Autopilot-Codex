import Link from "next/link";

import { fetchJson } from "@/lib/api";

type ArchivedItem = {
  id: string;
  plan_id: string;
  product_id: string;
  product_name: string;
  plan_month: string;
  plan_theme: string;
  title: string;
  angle: string | null;
  article_type: string;
  status: string;
  target_keywords: string[];
  scheduled_at?: string | null;
  published_at?: string | null;
  updated_at: string;
  generated_draft_title?: string | null;
  generated_draft_markdown?: string | null;
};

function getBadgeClass(status: string) {
  const normalized = status.toLowerCase();
  if (normalized === "published") return "badge badge-success";
  if (normalized === "archived") return "badge badge-outline";
  return "badge badge-info";
}

function getStatusLabel(status: string) {
  if (status === "published") return "Опубликовано";
  if (status === "archived") return "Архив";
  return status;
}

export default async function ArchivePage({
  searchParams,
}: {
  searchParams: Promise<{ query?: string; product_id?: string }>;
}) {
  const { query = "", product_id = "" } = await searchParams;
  const suffix = new URLSearchParams(
    Object.entries({
      query,
      product_id,
    }).filter(([, value]) => value),
  ).toString();
  const items = await fetchJson<ArchivedItem[]>(`/content-plans/archive/items${suffix ? `?${suffix}` : ""}`, []);

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">История материалов</p>
          <h1>Архив</h1>
        </div>
      </header>

      <section className="panel">
        <form method="GET" style={{ display: "grid", gap: "12px", gridTemplateColumns: "1fr auto" }}>
          <input
            type="search"
            name="query"
            defaultValue={query}
            className="form-input"
            placeholder="Поиск"
          />
          <button type="submit" className="btn btn-primary">
            Найти
          </button>
        </form>
      </section>

      <section className="panel" style={{ marginTop: "20px" }}>
        <div className="panel-header">
          <div>
            <span className="panel-kicker">Материалы</span>
            <h2 className="panel-title">Всего: {items.length}</h2>
          </div>
        </div>

        <div className="list-container">
          {items.length > 0 ? (
            items.map((item) => (
              <div key={item.id} className="list-item" style={{ alignItems: "flex-start", padding: "20px 0" }}>
                <div style={{ flex: 1, display: "grid", gap: "12px" }}>
                  <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", alignItems: "center" }}>
                    <span className={getBadgeClass(item.status)}>{getStatusLabel(item.status)}</span>
                    <span className="badge badge-outline">{item.article_type}</span>
                    <span className="badge badge-outline">{item.product_name}</span>
                    <span className="badge badge-outline">{item.plan_month}</span>
                  </div>
                  <div>
                    <Link href={`/content-plans/${item.plan_id}/items/${item.id}`} className="item-link">
                      {item.generated_draft_title || item.title}
                    </Link>
                    <p className="form-hint" style={{ marginTop: "8px" }}>
                      {item.angle || item.plan_theme || "Без описания"}
                    </p>
                  </div>
                  <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                    {item.target_keywords.map((keyword) => (
                      <span key={keyword} className="badge badge-outline" style={{ fontSize: "0.72rem" }}>
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>

                <div style={{ minWidth: "240px", display: "grid", gap: "8px", justifyItems: "end" }}>
                  {item.published_at ? (
                    <span className="form-hint">Опубликовано: {new Date(item.published_at).toLocaleString("ru-RU")}</span>
                  ) : null}
                  {item.scheduled_at ? (
                    <span className="form-hint">Было в плане: {new Date(item.scheduled_at).toLocaleString("ru-RU")}</span>
                  ) : null}
                  <span className="form-hint">Обновлено: {new Date(item.updated_at).toLocaleString("ru-RU")}</span>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state">
              <h3>Архив пока пуст</h3>
            </div>
          )}
        </div>
      </section>
    </>
  );
}
