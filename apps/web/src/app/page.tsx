import Link from "next/link";

import { fetchJson } from "@/lib/api";

export const dynamic = "force-dynamic";

type Product = {
  id: string;
  name: string;
  slug: string;
  category: string | null;
  lifecycle_stage: string | null;
  short_description: string | null;
  is_active: boolean;
  primary_channels: string[];
  content_settings?: {
    autopilot_enabled?: boolean;
    articles_per_month?: number;
  } | null;
};

function prettifyChannel(channel: string) {
  const labels: Record<string, string> = {
    blog: "Блог",
    telegram: "Telegram",
    instagram: "Instagram",
    youtube: "YouTube",
    vk: "VK",
    linkedin: "LinkedIn",
    x: "X",
  };

  return labels[channel] || channel;
}

function prettifyCategory(category: string | null) {
  if (!category) return "Без категории";

  const labels: Record<string, string> = {
    "personal-brand": "Личный бренд",
    service: "Услуга",
    product: "Продукт",
    media: "Медиа",
    education: "Обучение",
  };

  return labels[category] || category;
}

function prettifyLifecycleStage(stage: string | null) {
  if (!stage) return "Стадия не указана";

  const labels: Record<string, string> = {
    draft: "Черновой этап",
    active: "В работе",
    launched: "Запущен",
    growth: "Рост",
    paused: "На паузе",
  };

  return labels[stage] || stage;
}

function formatPublishingPace(articlesPerMonth?: number) {
  if (!articlesPerMonth) return "Частота публикаций не задана";
  if (articlesPerMonth === 1) return "1 материал в месяц";
  if (articlesPerMonth >= 2 && articlesPerMonth <= 4) return `${articlesPerMonth} материала в месяц`;
  return `${articlesPerMonth} материалов в месяц`;
}

export default async function HomePage() {
  const products = await fetchJson<Product[]>("/products", []);
  const activeProducts = products.filter((product) => product.is_active);

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">Athena Content OS</p>
          <h1>Дашборд</h1>
        </div>
        <div style={{ display: "flex", gap: "12px" }}>
          <Link href="/settings" className="btn">
            Настройки
          </Link>
          <Link href="/products/new" className="btn btn-primary">
            + Новый продукт
          </Link>
        </div>
      </header>

      <section className="product-tree">
        {activeProducts.length > 0 ? (
          activeProducts.map((product) => (
            <Link key={product.id} href={`/products/${product.id}`} className="product-node">
              <div className="product-node-top">
                <span className="panel-kicker">Продукт</span>
                <span className="badge badge-success">Активен</span>
              </div>

              <h2 className="product-node-title">{product.name}</h2>
              <p className="product-node-description">{product.short_description || "Без описания"}</p>

              <div className="product-node-meta">
                <span>{prettifyCategory(product.category)}</span>
                <span>{prettifyLifecycleStage(product.lifecycle_stage)}</span>
                <span>{product.content_settings?.autopilot_enabled ? "Автопилот включён" : "Автопилот выключен"}</span>
                <span>{formatPublishingPace(product.content_settings?.articles_per_month)}</span>
              </div>

              <div className="product-node-channels">
                {product.primary_channels.length > 0 ? (
                  product.primary_channels.map((channel) => (
                    <span key={channel} className="badge badge-outline">
                      {prettifyChannel(channel)}
                    </span>
                  ))
                ) : (
                  <span className="badge badge-outline">Каналы не заданы</span>
                )}
              </div>

              <div className="product-node-link">
                <span>Открыть продукт</span>
                <span aria-hidden="true">→</span>
              </div>
            </Link>
          ))
        ) : (
          <article className="panel">
            <div className="empty-state">
              <strong>Активных продуктов пока нет</strong>
            </div>
          </article>
        )}
      </section>
    </>
  );
}
