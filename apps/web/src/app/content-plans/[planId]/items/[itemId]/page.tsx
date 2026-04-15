import Link from "next/link";
import { revalidatePath } from "next/cache";

import { fetchJson, postJson, statusLabel } from "@/lib/api";

type ContentPlanItemDetail = {
  id: string;
  plan_id: string;
  order: number;
  title: string;
  angle: string | null;
  target_keywords: string[];
  article_type: string;
  cta_type: string;
  status: string;
  article_review: Record<string, unknown>;
  research_data: Record<string, unknown>;
  generated_draft_title: string | null;
  generated_draft_markdown: string | null;
  generated_summary: string | null;
  generated_hook: string | null;
  generated_cta: string | null;
  generation_mode: string | null;
};

type JobRunResponse = {
  item_status: string;
};

function getAllowedActions(status: string): string[] {
  if (status === "planned") return ["generate"];
  if (status === "draft") return ["review-ready", "planned"];
  if (status === "review-ready") return ["draft", "published", "failed"];
  if (status === "failed") return ["planned", "draft"];
  return [];
}

async function startGenerationAction(formData: FormData) {
  "use server";

  const planId = String(formData.get("planId"));
  const itemId = String(formData.get("itemId"));
  const path = `/content-plans/${planId}/items/${itemId}`;

  await postJson<JobRunResponse>(`/job-runs/content-plans/${planId}/items/${itemId}/start-generation`, {
    notes: "Triggered from content item detail UI",
  });

  revalidatePath(path);
  revalidatePath("/");
}

async function updateStatusAction(formData: FormData) {
  "use server";

  const planId = String(formData.get("planId"));
  const itemId = String(formData.get("itemId"));
  const status = String(formData.get("status"));
  const path = `/content-plans/${planId}/items/${itemId}`;

  await postJson<ContentPlanItemDetail>(`/content-plans/${planId}/items/${itemId}/status`, {
    status,
  });

  revalidatePath(path);
  revalidatePath("/");
}

export default async function ContentPlanItemPage({
  params,
}: {
  params: Promise<{ planId: string; itemId: string }>;
}) {
  const { planId, itemId } = await params;
  const item = await fetchJson<ContentPlanItemDetail | null>(
    `/content-plans/${planId}/items/${itemId}`,
    null,
  );

  if (!item) {
    return (
      <main className="page-shell">
        <section className="hero">
          <p className="eyebrow">Content Item</p>
          <h1>Элемент плана не найден</h1>
          <p className="lead">Похоже, API еще не поднят или этот item не существует.</p>
          <Link href="/" className="inline-link">
            Вернуться в dashboard
          </Link>
        </section>
      </main>
    );
  }

  const actions = getAllowedActions(item.status);
  const reviewNotes = Array.isArray(item.article_review?.review_notes)
    ? (item.article_review.review_notes as string[])
    : [];
  const generationPayload =
    typeof item.research_data?.generation_payload === "object" && item.research_data?.generation_payload
      ? (item.research_data.generation_payload as Record<string, unknown>)
      : null;

  return (
    <main className="page-shell dashboard-shell">
      <section className="hero dashboard-hero">
        <div>
          <p className="eyebrow">Content Item</p>
          <h1>{item.generated_draft_title || item.title}</h1>
          <p className="lead">
            Item #{item.order + 1} · {statusLabel(item.status)} · {item.article_type} · {item.cta_type}
          </p>
        </div>
        <div className="hero-panel">
          <span className="panel-label">Generation mode</span>
          <strong>{item.generation_mode || "not generated yet"}</strong>
          <p>{item.generated_summary || "Сначала нужно запустить generation или открыть уже сгенерированный draft."}</p>
        </div>
      </section>

      <section className="detail-page-grid">
        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Actions</p>
              <h2>Lifecycle</h2>
            </div>
          </div>
          <div className="action-stack">
            {actions.includes("generate") ? (
              <form action={startGenerationAction}>
                <input type="hidden" name="planId" value={planId} />
                <input type="hidden" name="itemId" value={itemId} />
                <button type="submit" className="action-button action-primary">
                  Run generation
                </button>
              </form>
            ) : null}

            {actions
              .filter((action) => action !== "generate")
              .map((action) => (
                <form action={updateStatusAction} key={action}>
                  <input type="hidden" name="planId" value={planId} />
                  <input type="hidden" name="itemId" value={itemId} />
                  <input type="hidden" name="status" value={action} />
                  <button type="submit" className="action-button">
                    Move to {statusLabel(action)}
                  </button>
                </form>
              ))}

            <Link href={`/content-plans/${planId}`} className="inline-link">
              Вернуться к content plan
            </Link>
            <Link href="/" className="inline-link">
              Вернуться в dashboard
            </Link>
          </div>
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Brief</p>
              <h2>Контекст item-а</h2>
            </div>
          </div>
          <div className="detail-stack">
            <div>
              <span className="detail-label">Title</span>
              <strong>{item.title}</strong>
            </div>
            <div>
              <span className="detail-label">Angle</span>
              <p>{item.angle || "Не задано."}</p>
            </div>
            <div>
              <span className="detail-label">Keywords</span>
              <p>{item.target_keywords.length > 0 ? item.target_keywords.join(" · ") : "Не заданы."}</p>
            </div>
          </div>
        </article>

        <article className="panel panel-wide">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Draft</p>
              <h2>Сгенерированный результат</h2>
            </div>
          </div>
          {item.generated_draft_markdown ? (
            <div className="draft-stack">
              <div className="draft-meta-grid">
                <div className="mini-card">
                  <span className="detail-label">Hook</span>
                  <p>{item.generated_hook || "Не заполнен."}</p>
                </div>
                <div className="mini-card">
                  <span className="detail-label">CTA</span>
                  <p>{item.generated_cta || "Не заполнен."}</p>
                </div>
              </div>
              <article className="draft-preview">
                <pre>{item.generated_draft_markdown}</pre>
              </article>
            </div>
          ) : (
            <div className="empty-state">
              <strong>Draft пока не сгенерирован</strong>
              <p>Этот экран станет рабочим после первого generation run для item-а.</p>
            </div>
          )}
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Review</p>
              <h2>Review notes</h2>
            </div>
          </div>
          {reviewNotes.length > 0 ? (
            <ul className="later-list">
              {reviewNotes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          ) : (
            <div className="empty-state">
              <strong>Review notes пока нет</strong>
              <p>Они появятся после generation run и первого review pass.</p>
            </div>
          )}
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Payload</p>
              <h2>Structured output</h2>
            </div>
          </div>
          <article className="json-preview">
            <pre>{JSON.stringify(generationPayload, null, 2)}</pre>
          </article>
        </article>
      </section>
    </main>
  );
}
