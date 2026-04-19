import Link from "next/link";
import { revalidatePath } from "next/cache";

import { fetchJson, postJson, statusLabel } from "@/lib/api";

type ContentPlanItem = {
  id: string;
  order: number;
  title: string;
  angle: string | null;
  status: string;
  article_type: string;
  cta_type: string;
  target_keywords: string[];
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
  const s = status.toLowerCase();
  if (["published", "completed"].includes(s)) return "badge badge-success";
  if (["draft", "planned"].includes(s)) return "badge badge-outline";
  if (["failed", "error"].includes(s)) return "badge badge-danger";
  if (["running", "in_progress"].includes(s)) return "badge badge-warning";
  if (["review-ready"].includes(s)) return "badge badge-info";
  return "badge badge-info";
}

async function generatePlanItemsAction(formData: FormData) {
  "use server";
  const planId = String(formData.get("planId"));
  const themeOverrideRaw = String(formData.get("themeOverride") || "").trim();
  const numItemsRaw = String(formData.get("numItems") || "").trim();
  const payload: { theme?: string; num_items?: number } = {};

  if (themeOverrideRaw) {
    payload.theme = themeOverrideRaw;
  }

  if (numItemsRaw) {
    const parsed = Number(numItemsRaw);
    if (Number.isFinite(parsed) && parsed > 0) {
      payload.num_items = parsed;
    }
  }

  await postJson(`/content-plans/${planId}/generate-items`, payload);
  revalidatePath(`/content-plans/${planId}`);
  revalidatePath("/");
}

async function runItemGenerationAction(formData: FormData) {
  "use server";
  const planId = String(formData.get("planId"));
  const itemId = String(formData.get("itemId"));
  await postJson(`/job-runs/content-plans/${planId}/items/${itemId}/start-generation`, {
    notes: "Triggered from content plan page",
  });
  revalidatePath(`/content-plans/${planId}`);
}

async function moveStatusAction(formData: FormData) {
  "use server";
  const planId = String(formData.get("planId"));
  const itemId = String(formData.get("itemId"));
  const status = String(formData.get("status"));
  await postJson(`/content-plans/${planId}/items/${itemId}/status`, { status });
  revalidatePath(`/content-plans/${planId}`);
}

export default async function ContentPlanPage({
  params,
}: {
  params: Promise<{ planId: string }>;
}) {
  const { planId } = await params;
  const plan = await fetchJson<ContentPlan | null>(`/content-plans/${planId}`, null);

  if (!plan) {
    return (
      <header className="page-header">
        <div>
          <h1>План не найден</h1>
          <p className="lead">Не удалось загрузить данные контент-плана.</p>
        </div>
      </header>
    );
  }

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">Контент-план: {plan.month}</p>
          <h1>{plan.theme || "План без фиксированной темы"}</h1>
          <p className="lead" style={{ marginTop: "12px", display: "flex", gap: "12px", alignItems: "center" }}>
            <span className={getBadgeClass(plan.status)}>{statusLabel(plan.status)}</span>
            <span>Темы: {plan.items.length}</span>
          </p>
        </div>
      </header>

      <section className="panel-grid" style={{ gridTemplateColumns: "1fr" }}>
        <article className="panel">
          <div className="panel-header" style={{ alignItems: "flex-start", gap: "20px" }}>
            <div style={{ flex: 1 }}>
              <span className="panel-kicker">Планирование</span>
              <h2 className="panel-title">Генерация тем</h2>
              <p className="form-hint" style={{ marginTop: "10px" }}>
                Оставь тему пустой, чтобы ИИ сам собрал идеи по контексту продукта. Или задай конкретную тему и число
                постов для отдельного спецблока вне обычного плана.
              </p>
            </div>
            <Link href="/" className="btn">
              ← На дашборд
            </Link>
          </div>

          <form action={generatePlanItemsAction} style={{ display: "grid", gap: "16px", gridTemplateColumns: "1fr 180px auto" }}>
            <input type="hidden" name="planId" value={plan.id} />
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Спецтема</label>
              <input
                type="text"
                name="themeOverride"
                className="form-input"
                placeholder="Например: Что бизнесу реально даёт новый AI-агент"
              />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Сколько постов</label>
              <input type="number" name="numItems" className="form-input" min={1} max={30} placeholder="Авто" />
            </div>
            <div style={{ display: "flex", alignItems: "end" }}>
              <button type="submit" className="btn btn-primary" title="ИИ предложит новые темы">
                Сгенерировать темы
              </button>
            </div>
          </form>
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">Пайплайн</span>
              <h2 className="panel-title">Очередь контента</h2>
            </div>
          </div>

          <div className="list-container">
            {plan.items.length > 0 ? (
              plan.items.map((item) => (
                <div key={item.id} className="list-item" style={{ alignItems: "flex-start", padding: "24px 0" }}>
                  <div style={{ paddingRight: "40px" }}>
                    <span className="list-item-sub" style={{ display: "block", marginBottom: "8px" }}>
                      #{item.order + 1} • {item.article_type}
                    </span>
                    <strong className="list-item-title" style={{ fontSize: "1.1rem" }}>
                      {item.title}
                    </strong>
                    <p style={{ color: "var(--muted)", margin: "8px 0", fontSize: "0.9rem", maxWidth: "800px" }}>
                      {item.angle || "Угол подачи не задан."}
                    </p>
                    <div style={{ display: "flex", gap: "8px", marginTop: "12px", flexWrap: "wrap" }}>
                      {item.target_keywords.map((kw) => (
                        <span key={kw} className="badge badge-outline" style={{ fontSize: "0.7rem" }}>
                          {kw}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "12px", minWidth: "200px" }}>
                    <span className={getBadgeClass(item.status)}>{statusLabel(item.status)}</span>
                    <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", justifyContent: "flex-end" }}>
                      <Link href={`/content-plans/${plan.id}/items/${item.id}`} className="btn">
                        Редактор
                      </Link>
                      {item.status === "planned" && (
                        <form action={runItemGenerationAction}>
                          <input type="hidden" name="planId" value={plan.id} />
                          <input type="hidden" name="itemId" value={item.id} />
                          <button type="submit" className="btn btn-primary">
                            Создать черновик
                          </button>
                        </form>
                      )}
                      {item.status === "draft" && (
                        <form action={moveStatusAction}>
                          <input type="hidden" name="planId" value={plan.id} />
                          <input type="hidden" name="itemId" value={item.id} />
                          <input type="hidden" name="status" value="review-ready" />
                          <button type="submit" className="btn">
                            На проверку
                          </button>
                        </form>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <strong>В очереди пока пусто</strong>
                <p>Нажмите «Сгенерировать темы», чтобы автопилот предложил идеи постов.</p>
              </div>
            )}
          </div>
        </article>
      </section>
    </>
  );
}
