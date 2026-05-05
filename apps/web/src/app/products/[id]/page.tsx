import Link from "next/link";
import { revalidatePath } from "next/cache";

import HelpHint from "@/components/HelpHint";
import SubmitButton from "@/components/SubmitButton";
import { deleteJson, fetchJson, patchJson, statusLabel } from "@/lib/api";

import ProductChannelsPanel from "./ProductChannelsPanel";
import ProductContextForm from "./ProductContextForm";
import ProductPlanForm from "./ProductPlanForm";

type ProductPageProps = {
  params: Promise<{ id: string }>;
};

type ProductContentSettings = {
  autopilot_enabled: boolean;
  social_posting_enabled: boolean;
  articles_per_month: number;
};

type ProductChannel = {
  id: string;
  platform: string;
  name: string;
  settings_json: Record<string, string>;
  external_id: string | null;
  external_name: string | null;
  validation_status: string;
  validation_message: string | null;
  validated_at: string | null;
  is_active: boolean;
  configured_secret_keys: string[];
};

type Product = {
  id: string;
  name: string;
  short_description: string | null;
  full_description: string | null;
  tone_of_voice: string | null;
  target_audience: string | null;
  primary_channels: string[];
  channels: ProductChannel[];
  content_settings: ProductContentSettings | null;
};

type ContentPlanItem = {
  id: string;
  title: string;
  status: string;
};

type ContentPlan = {
  id: string;
  product_id: string;
  month: string;
  theme: string | null;
  status: string;
  items: ContentPlanItem[];
};

function getBadgeClass(status: string) {
  const normalized = status.toLowerCase();
  if (["published", "completed", "active"].includes(normalized)) return "badge badge-success";
  if (["draft", "planned"].includes(normalized)) return "badge badge-outline";
  if (["failed", "error"].includes(normalized)) return "badge badge-danger";
  if (["running", "in_progress", "pending"].includes(normalized)) return "badge badge-warning";
  if (["review-ready"].includes(normalized)) return "badge badge-info";
  return "badge badge-info";
}

async function deletePlanAction(formData: FormData) {
  "use server";
  const productId = String(formData.get("productId"));
  const planId = String(formData.get("planId"));

  await deleteJson(`/content-plans/${planId}`);

  revalidatePath(`/products/${productId}`);
  revalidatePath("/");
}

async function toggleAutopostAction(formData: FormData) {
  "use server";
  const productId = String(formData.get("productId"));
  const enabled = formData.get("enabled") === "on";

  await patchJson(`/products/${productId}/settings`, {
    autopilot_enabled: enabled,
    social_posting_enabled: enabled,
  });

  revalidatePath(`/products/${productId}`);
  revalidatePath("/");
}

export default async function ProductPage({ params }: ProductPageProps) {
  const { id: productId } = await params;

  const [product, contentPlans] = await Promise.all([
    fetchJson<Product | null>(`/products/${productId}`, null),
    fetchJson<ContentPlan[]>("/content-plans", []),
  ]);

  if (!product) {
    return <div className="empty-state">Продукт не найден.</div>;
  }

  const productPlans = contentPlans.filter((plan) => plan.product_id === productId).sort((a, b) => b.month.localeCompare(a.month));
  const autopostEnabled = Boolean(product.content_settings?.autopilot_enabled && product.content_settings?.social_posting_enabled);

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">Продукт</p>
          <h1>{product.name}</h1>
          <p className="lead">{product.short_description || "Рабочее пространство продукта."}</p>
        </div>
      </header>

      <section className="panel-grid product-page-grid">
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          <article className="panel">
            <ProductChannelsPanel productId={productId} initialChannels={product.channels} />
          </article>

          <article className="panel">
            <div className="panel-header" style={{ alignItems: "flex-start", gap: "20px" }}>
              <div>
                <span className="panel-kicker">Планирование</span>
                <h2 className="panel-title" style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
                  Контент-планы
                  <HelpHint text="Здесь создаются планы, темы и материалы. Любой пост потом можно открыть, поправить или удалить вручную." />
                </h2>
              </div>
              <span className="badge badge-accent">{productPlans.length}</span>
            </div>

            <form
              action={toggleAutopostAction}
              style={{
                display: "flex",
                justifyContent: "space-between",
                gap: "16px",
                alignItems: "center",
                flexWrap: "wrap",
                padding: "16px 18px",
                marginBottom: "20px",
                borderRadius: "16px",
                border: "1px solid var(--border)",
                background: "rgba(255,255,255,0.03)",
              }}
            >
              <input type="hidden" name="productId" value={productId} />
              <div style={{ maxWidth: "720px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
                  <strong style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
                    <span>Автопостинг</span>
                    <HelpHint text="Автопилот сам собирает материалы и публикует их по расписанию. Ручное редактирование и удаление материалов остаётся доступным." />
                  </strong>
                  <span className={autopostEnabled ? "badge badge-success" : "badge badge-outline"}>
                    {autopostEnabled ? "Включён" : "Выключен"}
                  </span>
                </div>
              </div>

              <label style={{ display: "flex", alignItems: "center", gap: "10px", color: "var(--text)" }}>
                <input type="checkbox" name="enabled" defaultChecked={autopostEnabled} />
                <span>Разрешить автопостинг</span>
              </label>

              <SubmitButton className="btn" pendingLabel="Сохраняем режим...">
                Сохранить режим
              </SubmitButton>
            </form>

            <div className="list-container" style={{ marginBottom: "20px" }}>
              {productPlans.length > 0 ? (
                productPlans.map((plan) => (
                  <div key={plan.id} className="list-item compact-list-item">
                    <div>
                      <Link href={`/content-plans/${plan.id}`} className="list-item-title item-link" style={{ textDecoration: "none" }}>
                        {plan.theme || "План без фиксированной темы"}
                      </Link>
                      <span className="list-item-sub">
                        {plan.month} · {plan.items.length} тем
                      </span>
                    </div>

                    <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap", justifyContent: "flex-end" }}>
                      <span className={getBadgeClass(plan.status)}>{statusLabel(plan.status)}</span>
                      <Link href={`/content-plans/${plan.id}`} className="btn btn-sm">
                        Открыть
                      </Link>
                      <form action={deletePlanAction}>
                        <input type="hidden" name="productId" value={productId} />
                        <input type="hidden" name="planId" value={plan.id} />
                        <SubmitButton
                          className="btn btn-sm"
                          style={{ borderColor: "var(--danger)", color: "var(--danger)" }}
                          pendingLabel="Удаляем..."
                        >
                          Удалить
                        </SubmitButton>
                      </form>
                    </div>
                  </div>
                ))
              ) : (
                <div className="empty-state compact-empty-state">
                  <strong>Планов пока нет</strong>
                </div>
              )}
            </div>

            <ProductPlanForm productId={productId} />
          </article>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          <article className="panel">
            <details className="panel-details">
              <summary className="panel-details-summary">
                <div>
                  <span className="panel-kicker">База знаний</span>
                  <h2 className="panel-title">Контекст и стратегия продукта</h2>
                </div>
                <span className="badge badge-outline">Развернуть</span>
              </summary>

              <div style={{ marginTop: "20px" }}>
                <ProductContextForm
                  productId={productId}
                  initialFullDescription={product.full_description || ""}
                  initialToneOfVoice={product.tone_of_voice || ""}
                  initialTargetAudience={product.target_audience || ""}
                />
              </div>
            </details>
          </article>

          <article className="panel">
            <div className="panel-header">
              <div>
                <span className="panel-kicker">Research</span>
                <h2 className="panel-title">Мониторинг конкурентов</h2>
              </div>
              <span className="badge badge-outline">Скоро</span>
            </div>

            <div className="empty-state compact-empty-state">
              <strong>Раздел готовится</strong>
            </div>
          </article>
        </div>
      </section>
    </>
  );
}
