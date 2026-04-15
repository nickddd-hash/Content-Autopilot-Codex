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
  items: Array<{ id: string; status: string }>;
};

type JobRun = {
  id: string;
  job_type: string;
  status: string;
  content_plan_item_id: string | null;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
  meta_json: Record<string, unknown>;
};

export default async function HomePage() {
  const [summary, products, brandProfile, contentPlans, jobRuns] = await Promise.all([
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
    fetchJson<JobRun[]>("/job-runs?limit=6", []),
  ]);

  const metrics = [
    { label: "Продукты", value: summary.total_products, hint: `${summary.active_products} активных` },
    { label: "Автопилот", value: summary.autopilot_enabled_products, hint: "включено продуктов" },
    { label: "Контент-планы", value: summary.total_content_plans, hint: `${summary.planned_items} элементов planned` },
    { label: "Ошибки", value: summary.failed_items, hint: `${summary.running_jobs} задач сейчас running` },
  ];

  return (
    <main className="page-shell dashboard-shell">
      <section className="hero dashboard-hero">
        <div>
          <p className="eyebrow">Content Autopilot</p>
          <h1>Операционный dashboard контентной системы</h1>
          <p className="lead">
            В первой версии нам нужен не промо-экран, а понятный центр управления:
            продукты, стратегия бренда, контент-планы и общее состояние пайплайна.
          </p>
        </div>
        <div className="hero-panel">
          <span className="panel-label">Текущий фокус</span>
          <strong>V1 Core</strong>
          <p>Product, Brand Profile, Content Plan, Dashboard и ручной generation flow.</p>
        </div>
      </section>

      <section className="stats-grid">
        {metrics.map((metric) => (
          <article key={metric.label} className="stat-card">
            <span className="stat-label">{metric.label}</span>
            <strong className="stat-value">{metric.value}</strong>
            <p className="stat-hint">{metric.hint}</p>
          </article>
        ))}
      </section>

      <section className="dashboard-grid">
        <article className="panel panel-wide">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Продукты</p>
              <h2>Активные продукты и каналы</h2>
            </div>
            <span className="panel-badge">{products.length} всего</span>
          </div>
          <div className="list-stack">
            {products.length > 0 ? (
              products.map((product) => (
                <div key={product.id} className="list-item">
                  <div>
                    <strong>{product.name}</strong>
                    <p>
                      {product.slug}
                      {product.category ? ` · ${product.category}` : ""}
                      {product.lifecycle_stage ? ` · ${product.lifecycle_stage}` : ""}
                    </p>
                  </div>
                  <div className="item-meta">
                    <span className={`chip ${product.is_active ? "chip-active" : ""}`}>
                      {product.is_active ? "Активен" : "Выключен"}
                    </span>
                    <span className="muted-inline">
                      {product.primary_channels.length > 0
                        ? product.primary_channels.join(", ")
                        : "Каналы еще не заданы"}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <strong>Продукты пока не заведены</strong>
                <p>Следующий рабочий шаг: создать первый реальный Product и связанный Brand Profile.</p>
              </div>
            )}
          </div>
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Brand Profile</p>
              <h2>Стратегия бренда</h2>
            </div>
          </div>
          {brandProfile ? (
            <div className="detail-stack">
              <div>
                <span className="detail-label">Brand</span>
                <strong>{brandProfile.brand_name || "Без названия"}</strong>
              </div>
              <div>
                <span className="detail-label">Summary</span>
                <p>{brandProfile.brand_summary || "Краткое позиционирование пока не заполнено."}</p>
              </div>
              <div>
                <span className="detail-label">Core messages</span>
                <p>
                  {brandProfile.core_messages.length > 0
                    ? brandProfile.core_messages.join(" · ")
                    : "Сообщения бренда еще не заданы."}
                </p>
              </div>
              <div>
                <span className="detail-label">Channel strategy</span>
                <p>
                  {Object.keys(brandProfile.channel_strategy).length > 0
                    ? Object.entries(brandProfile.channel_strategy)
                        .map(([channel, strategy]) => `${channel}: ${strategy}`)
                        .join(" | ")
                    : "Стратегия по каналам еще не заполнена."}
                </p>
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <strong>Brand Profile еще пустой</strong>
              <p>Для v1 это одна из главных сущностей: без нее автопилот не понимает голос и правила бренда.</p>
            </div>
          )}
        </article>

        <article className="panel panel-wide">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Content Plans</p>
              <h2>Планы и их состояние</h2>
            </div>
            <span className="panel-badge">{contentPlans.length} планов</span>
          </div>
          <div className="list-stack">
            {contentPlans.length > 0 ? (
              contentPlans.map((plan) => (
                <div key={plan.id} className="list-item">
                  <div>
                    <strong>{plan.theme}</strong>
                    <p>{plan.month}</p>
                    <div className="item-link-list">
                      <Link href={`/content-plans/${plan.id}`} className="item-link">
                        Открыть план
                      </Link>
                    </div>
                    {plan.items.length > 0 ? (
                      <div className="item-link-list">
                        {plan.items.map((item, index) => (
                          <Link
                            key={item.id}
                            href={`/content-plans/${plan.id}/items/${item.id}`}
                            className="item-link"
                          >
                            Item {index + 1} · {statusLabel(item.status)}
                          </Link>
                        ))}
                      </div>
                    ) : null}
                  </div>
                  <div className="item-meta">
                    <span className="chip">{statusLabel(plan.status)}</span>
                    <span className="muted-inline">{plan.items.length} items</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <strong>Пока нет ни одного контент-плана</strong>
                <p>После продуктов и brand profile это следующая опорная сущность текущей версии.</p>
              </div>
            )}
          </div>
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Generation Jobs</p>
              <h2>Последние ручные запуски</h2>
            </div>
          </div>
          <div className="list-stack compact-stack">
            {jobRuns.length > 0 ? (
              jobRuns.map((job) => (
                <div key={job.id} className="list-item compact-item">
                  <div>
                    <strong>{job.job_type}</strong>
                    <p>{job.meta_json.result || job.meta_json.stage || "manual run"}</p>
                  </div>
                  <div className="item-meta">
                    <span className="chip">{statusLabel(job.status)}</span>
                    <span className="muted-inline">
                      {job.finished_at ? "завершен" : job.started_at ? "в процессе" : "создан"}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <strong>Запусков пока нет</strong>
                <p>Следующий шаг после bootstrap: запускать generation jobs для элементов контент-плана.</p>
              </div>
            )}
          </div>
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Later</p>
              <h2>Что не тащим в V1</h2>
            </div>
          </div>
          <ul className="later-list">
            <li>Instagram parser и ingestion чужих постов</li>
            <li>Parser видео, Reels и Shorts</li>
            <li>Trend / viral monitoring</li>
            <li>Rewrite внешнего контента как отдельный pipeline</li>
            <li>Полный production scheduler и автопостинг</li>
          </ul>
        </article>
      </section>
    </main>
  );
}

