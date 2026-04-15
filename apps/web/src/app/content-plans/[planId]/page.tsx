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
  theme: string;
  status: string;
  items: ContentPlanItem[];
};

type JobRunResponse = {
  item_status: string;
};

function getQuickActions(status: string): string[] {
  if (status === "planned") return ["generate"];
  if (status === "draft") return ["review-ready"];
  if (status === "review-ready") return ["published", "failed"];
  if (status === "failed") return ["draft"];
  return [];
}

async function runGenerationAction(formData: FormData) {
  "use server";

  const planId = String(formData.get("planId"));
  const itemId = String(formData.get("itemId"));

  await postJson<JobRunResponse>(`/job-runs/content-plans/${planId}/items/${itemId}/start-generation`, {
    notes: "Triggered from content plan page",
  });

  revalidatePath(`/content-plans/${planId}`);
  revalidatePath(`/content-plans/${planId}/items/${itemId}`);
  revalidatePath("/");
}

async function moveStatusAction(formData: FormData) {
  "use server";

  const planId = String(formData.get("planId"));
  const itemId = String(formData.get("itemId"));
  const status = String(formData.get("status"));

  await postJson(`/content-plans/${planId}/items/${itemId}/status`, { status });

  revalidatePath(`/content-plans/${planId}`);
  revalidatePath(`/content-plans/${planId}/items/${itemId}`);
  revalidatePath("/");
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
      <main className="page-shell">
        <section className="hero">
          <p className="eyebrow">Content Plan</p>
          <h1>План не найден</h1>
          <p className="lead">Похоже, API еще не поднят или этого content plan нет.</p>
          <Link href="/" className="inline-link">
            Вернуться в dashboard
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="page-shell dashboard-shell">
      <section className="hero dashboard-hero">
        <div>
          <p className="eyebrow">Content Plan</p>
          <h1>{plan.theme}</h1>
          <p className="lead">
            {plan.month} · {statusLabel(plan.status)} · {plan.items.length} items
          </p>
        </div>
        <div className="hero-panel">
          <span className="panel-label">Plan focus</span>
          <strong>{plan.theme}</strong>
          <p>Этот экран нужен как рабочий слой между общим dashboard и detail каждого item-а.</p>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="panel-kicker">Items</p>
            <h2>Элементы контент-плана</h2>
          </div>
          <Link href="/" className="inline-link">
            Вернуться в dashboard
          </Link>
        </div>

        <div className="list-stack">
          {plan.items.map((item) => {
            const quickActions = getQuickActions(item.status);

            return (
              <div key={item.id} className="list-item list-item-stacked">
                <div className="item-main">
                  <strong>
                    {item.order + 1}. {item.title}
                  </strong>
                  <p>
                    {statusLabel(item.status)} · {item.article_type} · {item.cta_type}
                  </p>
                  <p>{item.angle || "Угол подачи пока не заполнен."}</p>
                  <div className="item-link-list">
                    {item.target_keywords.map((keyword) => (
                      <span key={keyword} className="chip">
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="item-actions">
                  <Link
                    href={`/content-plans/${plan.id}/items/${item.id}`}
                    className="action-button action-link"
                  >
                    Открыть item
                  </Link>

                  {quickActions.includes("generate") ? (
                    <form action={runGenerationAction}>
                      <input type="hidden" name="planId" value={plan.id} />
                      <input type="hidden" name="itemId" value={item.id} />
                      <button type="submit" className="action-button action-primary">
                        Run generation
                      </button>
                    </form>
                  ) : null}

                  {quickActions
                    .filter((action) => action !== "generate")
                    .map((action) => (
                      <form action={moveStatusAction} key={action}>
                        <input type="hidden" name="planId" value={plan.id} />
                        <input type="hidden" name="itemId" value={item.id} />
                        <input type="hidden" name="status" value={action} />
                        <button type="submit" className="action-button">
                          Move to {statusLabel(action)}
                        </button>
                      </form>
                    ))}
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </main>
  );
}
