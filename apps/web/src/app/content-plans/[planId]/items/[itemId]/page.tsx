import Link from "next/link";
import { revalidatePath } from "next/cache";
import { fetchJson, postJson, statusLabel } from "@/lib/api";
import JobPolling from "./JobPolling";

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
  if (status === "draft") return ["generate", "review-ready", "planned"];
  if (status === "review-ready") return ["draft", "published", "failed"];
  if (status === "failed") return ["planned", "draft"];
  return [];
}

function getBadgeClass(status: string) {
  const s = status.toLowerCase();
  if (["published", "completed"].includes(s)) return "badge badge-success";
  if (["draft", "planned"].includes(s)) return "badge badge-outline";
  if (["failed", "error"].includes(s)) return "badge badge-danger";
  if (["running", "in_progress"].includes(s)) return "badge badge-warning";
  if (["review-ready"].includes(s)) return "badge badge-info";
  return "badge badge-info";
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

async function startVideoGenerationAction(formData: FormData) {
  "use server";
  const planId = String(formData.get("planId"));
  const itemId = String(formData.get("itemId"));
  // This is a stub action. In the future, this will call the video generation API.
  console.log(`[STUB] Started video generation for ${itemId}`);
  revalidatePath(`/content-plans/${planId}/items/${itemId}`);
}

async function startRewriteAction(formData: FormData) {
  "use server";
  const planId = String(formData.get("planId"));
  const itemId = String(formData.get("itemId"));
  const url = String(formData.get("url"));
  // This is a stub action. In the future, this will call the rewrite API.
  console.log(`[STUB] Started rewrite for ${itemId} using url ${url}`);
  revalidatePath(`/content-plans/${planId}/items/${itemId}`);
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
      <header className="page-header">
        <div>
          <h1>Элемент не найден</h1>
          <p className="lead">Не удалось загрузить данные темы контент-плана.</p>
        </div>
      </header>
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
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">
            <Link href={`/content-plans/${planId}`} className="item-link" style={{marginRight: '8px'}}>План</Link> 
            / Тема #{item.order + 1}
          </p>
          <h1>{item.generated_draft_title || item.title}</h1>
          <p className="lead" style={{ marginTop: "12px", display: "flex", gap: "12px", alignItems: "center" }}>
            <span className={getBadgeClass(item.status)}>{statusLabel(item.status)}</span>
            <span>{item.article_type}</span>
            <span className="badge badge-accent">{item.cta_type} CTA</span>
          </p>
        </div>
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
          {actions.includes("generate") && (
            <form action={startGenerationAction}>
              <input type="hidden" name="planId" value={planId} />
              <input type="hidden" name="itemId" value={itemId} />
              <button type="submit" className="btn btn-primary">
                {item.status === "draft" ? "Перегенерировать Текст" : "Создать текст"}
              </button>
            </form>
          )}
          {actions.includes("generate") && (
            <form action={startVideoGenerationAction}>
              <input type="hidden" name="planId" value={planId} />
              <input type="hidden" name="itemId" value={itemId} />
              <button type="submit" className="btn" style={{ borderColor: "var(--info)", color: "var(--info)" }}>
                Сгенерировать Видео
              </button>
            </form>
          )}
          {actions.includes("review-ready") && (
            <form action={updateStatusAction}>
               <input type="hidden" name="planId" value={planId} />
               <input type="hidden" name="itemId" value={itemId} />
               <input type="hidden" name="status" value="review-ready" />
               <button type="submit" className="btn">На проверку</button>
            </form>
          )}
          {actions.includes("published") && (
             <form action={updateStatusAction}>
               <input type="hidden" name="planId" value={planId} />
               <input type="hidden" name="itemId" value={itemId} />
               <input type="hidden" name="status" value="published" />
               <button type="submit" className="btn btn-primary">Опубликовано</button>
             </form>
          )}
        </div>
      </header>

      <section className="editor-layout">
        {/* Left Column: Editor & Content */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          <article className="panel">
            <div className="panel-header">
               <h2 className="panel-title">Черновик текста</h2>
            </div>
            {item.generated_draft_markdown ? (
              <div className="preview-box">
                <pre>{item.generated_draft_markdown}</pre>
              </div>
            ) : (
              <div className="empty-state">
                <strong>Текст еще не создан</strong>
                <p>Нажмите "Создать текст", чтобы AI подготовил первую версию материала.</p>
              </div>
            )}
          </article>
          
          <article className="panel">
            <div className="panel-header">
               <span className="panel-kicker">Альтернативный движок</span>
               <h2 className="panel-title">Rewrite Mode</h2>
            </div>
            <div style={{ padding: "16px", background: "rgba(255,255,255,0.02)", borderRadius: "16px", border: "1px dashed var(--border)" }}>
              <form action={startRewriteAction} style={{ display: "flex", gap: "12px", alignItems: "flex-end", flexWrap: "wrap" }}>
                <input type="hidden" name="planId" value={planId} />
                <input type="hidden" name="itemId" value={itemId} />
                <div style={{ flex: 1, minWidth: "250px" }}>
                  <label className="form-label">URL исходного материала (Конкурента)</label>
                  <input type="text" name="url" className="form-input" placeholder="https://example.com/competitor-article" required />
                </div>
                <button type="submit" className="btn btn-primary" style={{ height: "48px" }}>Переписать (Rewrite)</button>
              </form>
            </div>
          </article>

          <JobPolling planId={planId} itemId={itemId} initialStatus={item.status} />
        </div>

        {/* Right Column: Context, Review & Meta */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          <article className="panel">
            <div className="panel-header" style={{ marginBottom: "12px" }}>
              <span className="panel-kicker">Бриф и стратегия</span>
            </div>
            <div className="key-value-stack">
              <div className="kv-pair">
                <span className="kv-label">Тема</span>
                <span className="kv-val">{item.title}</span>
              </div>
              <div className="kv-pair">
                <span className="kv-label">Угол подачи</span>
                <span className="kv-val">{item.angle || "Не указан."}</span>
              </div>
              <div className="kv-pair">
                <span className="kv-label">Ключевые слова</span>
                <span className="kv-val">
                  {item.target_keywords.length > 0 ? (
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '4px' }}>
                      {item.target_keywords.map(kw => <span key={kw} className="badge badge-outline">{kw}</span>)}
                    </div>
                  ) : "Нет"}
                </span>
              </div>
              
              <hr style={{ borderColor: "var(--border)", margin: "12px 0" }} />

              <div className="kv-pair">
                <span className="kv-label">Сгенерированный хук</span>
                <span className="kv-val">{item.generated_hook || "—"}</span>
              </div>
              <div className="kv-pair">
                <span className="kv-label">Сгенерированный CTA</span>
                <span className="kv-val">{item.generated_cta || "—"}</span>
              </div>
            </div>
          </article>

          {reviewNotes.length > 0 && (
             <article className="panel">
               <div className="panel-header" style={{ marginBottom: "12px" }}>
                 <span className="panel-kicker">Заметки редактора</span>
               </div>
               <ul style={{ listStylePosition: "inside", padding: 0, margin: 0, color: "var(--text)" }}>
                 {reviewNotes.map((note, i) => (
                   <li key={i} style={{ marginBottom: "8px", fontSize: "0.9rem" }}>{note}</li>
                 ))}
               </ul>
             </article>
          )}

          {generationPayload && (
             <details style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "16px", padding: "16px" }}>
               <summary style={{ cursor: "pointer", fontWeight: "600", color: "var(--muted)", outline: "none" }}>Данные для разработчиков</summary>
               <div className="preview-box" style={{ marginTop: "16px" }}>
                 <pre>{JSON.stringify(generationPayload, null, 2)}</pre>
               </div>
             </details>
          )}
          
          <div style={{ marginTop: "12px", display: "flex", flexDirection: "column", gap: "8px" }}>
             {actions.map((action) => {
               if (action === "generate" || action === "review-ready" || action === "published") return null;
               return (
                 <form action={updateStatusAction} key={action} style={{ width: "100%" }}>
                   <input type="hidden" name="planId" value={planId} />
                   <input type="hidden" name="itemId" value={itemId} />
                   <input type="hidden" name="status" value={action} />
                   <button type="submit" className="btn" style={{ width: "100%" }}>
                     Перевести в {statusLabel(action)}
                   </button>
                 </form>
               );
             })}
          </div>
        </div>
      </section>
    </>
  );
}
