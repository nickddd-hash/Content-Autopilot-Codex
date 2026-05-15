import Link from "next/link";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import SubmitButton from "@/components/SubmitButton";
import { apiBaseUrl, fetchJson, patchJson, postJson, statusLabel } from "@/lib/api";
import JobPolling from "./JobPolling";

type ChannelAdaptation = {
  format?: string;
  content_markdown?: string;
  asset_brief?: string;
};

type GeneratedImage = {
  url?: string;
  prompt?: string;
  model?: string;
  mime_type?: string;
  generated_at?: string;
};

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
  channel_adaptations?: Record<string, ChannelAdaptation>;
  generation_mode: string | null;
  scheduled_at?: string | null;
  published_at?: string | null;
};

type JobRunResponse = {
  item_status: string;
};

function buildManualBriefFromDraft(draftTitle: string, draftMarkdown: string, regenNote?: string) {
  const sections: string[] = [];
  if (draftTitle) {
    sections.push(`Current working title, can be regenerated: ${draftTitle}`);
  }
  if (draftMarkdown) {
    sections.push(`Current draft or brief:\n${draftMarkdown}`);
  }
  if (regenNote) {
    sections.push(`Author note for this regeneration (follow strictly):\n${regenNote}`);
  }
  return sections.join("\n\n").trim();
}

function getBadgeClass(status: string) {
  const normalized = status.toLowerCase();
  if (["published", "completed"].includes(normalized)) return "badge badge-success";
  if (["archived"].includes(normalized)) return "badge badge-outline";
  if (["draft", "planned"].includes(normalized)) return "badge badge-outline";
  if (["failed", "error"].includes(normalized)) return "badge badge-danger";
  if (["running", "in_progress", "pending"].includes(normalized)) return "badge badge-warning";
  if (["review-ready"].includes(normalized)) return "badge badge-info";
  return "badge badge-info";
}

function getStatusLabel(status: string) {
  if (status === "archived") return "\u0410\u0440\u0445\u0438\u0432";
  return statusLabel(status);
}

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

function formatGenerationMode(mode: string | null) {
  if (!mode) return "Не указан";

  const labels: Record<string, string> = {
    llm_generated: "Сгенерировано через LLM",
    fallback_generated: "Сгенерировано через fallback",
  };

  return labels[mode] || mode;
}

function stripMarkdown(value: string) {
  return value
    .replace(/```[\s\S]*?```/g, (m) => m.replace(/`/g, "").trim())
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\*{1,3}([^*]+)\*{1,3}/g, "$1")
    .replace(/__([^_]+)__/g, "$1")
    .replace(/_([^_]+)_/g, "$1")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/^>\s*/gm, "")
    .replace(/^[-*_]{3,}\s*$/gm, "")
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
    .replace(/\n{3,}/g, "\n\n");
}

function normalizeEditorialText(value: string) {
  return stripMarkdown(value)
    .replace(/[—–]/g, "-")
    .replace(/\u00A0/g, " ")
    .replace(/\r\n/g, "\n")
    .trim();
}

function toDateTimeInputValue(value?: string | null) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";

  const formatter = new Intl.DateTimeFormat("sv-SE", {
    timeZone: "Europe/Moscow",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  });
  const parts = Object.fromEntries(
    formatter
      .formatToParts(date)
      .filter((part) => part.type !== "literal")
      .map((part) => [part.type, part.value]),
  ) as Record<string, string>;

  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
}

function normalizeScheduledAtInput(value: string) {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const withSeconds = trimmed.length === 16 ? `${trimmed}:00` : trimmed;
  return `${withSeconds}+03:00`;
}

async function startGenerationAction(formData: FormData) {
  "use server";
  const planId = String(formData.get("planId"));
  const itemId = String(formData.get("itemId"));
  const path = `/content-plans/${planId}/items/${itemId}`;

  await postJson<JobRunResponse>(`/content-plans/${planId}/items/${itemId}/generate`, {});

  revalidatePath(path);
  revalidatePath(`/content-plans/${planId}`);
  revalidatePath("/");
}

async function regenerateDraftAction(formData: FormData) {
  "use server";
  const planId = String(formData.get("planId"));
  const itemId = String(formData.get("itemId"));
  const path = `/content-plans/${planId}/items/${itemId}`;
  const draftTitle = normalizeEditorialText(String(formData.get("draftTitle") || ""));
  const draftMarkdown = normalizeEditorialText(String(formData.get("draftMarkdown") || ""));
  const regenNote = String(formData.get("regenNote") || "").trim();

  const current = await fetchJson<ContentPlanItemDetail | null>(`/content-plans/${planId}/items/${itemId}`, null);
  if (!current) {
    throw new Error("Content plan item not found");
  }

  const researchData =
    current.research_data && typeof current.research_data === "object" ? { ...current.research_data } : {};
  const currentPayload =
    researchData.generation_payload && typeof researchData.generation_payload === "object"
      ? { ...(researchData.generation_payload as Record<string, unknown>) }
      : {};

  researchData.manual_brief = buildManualBriefFromDraft(draftTitle, draftMarkdown, regenNote);
  researchData.regen_note = regenNote;
  researchData.generation_payload = {
    ...currentPayload,
    draft_title: draftTitle,
    draft_markdown: draftMarkdown,
  };

  await patchJson(`/content-plans/${planId}/items/${itemId}`, {
    title: draftTitle || current.title,
    status: "draft",
    research_data: researchData,
  });

  await postJson<JobRunResponse>(`/content-plans/${planId}/items/${itemId}/generate`, {});

  revalidatePath(path);
  revalidatePath(`/content-plans/${planId}`);
  revalidatePath("/");
  redirect(path);
}

async function publishItemAction(formData: FormData) {
  "use server";
  const planId = String(formData.get("planId"));
  const itemId = String(formData.get("itemId"));
  const path = `/content-plans/${planId}/items/${itemId}`;
  try {
    await postJson<ContentPlanItemDetail>(`/content-plans/${planId}/items/${itemId}/publish`, {});
  } catch (error) {
    const message = error instanceof Error ? error.message : "Не удалось опубликовать пост.";
    redirect(`${path}?publishError=${encodeURIComponent(message)}`);
  }

  revalidatePath(path);
  revalidatePath(`/content-plans/${planId}`);
  revalidatePath("/");
  redirect(path);
}

async function generateIllustrationAction(formData: FormData) {
  "use server";
  const planId = String(formData.get("planId"));
  const itemId = String(formData.get("itemId"));
  const path = `/content-plans/${planId}/items/${itemId}`;

  try {
    await postJson(`/content-plans/${planId}/items/${itemId}/generate-illustration`, {});
  } catch (error) {
    const message = error instanceof Error ? error.message : "Не удалось сгенерировать иллюстрацию.";
    redirect(`${path}?illustrationError=${encodeURIComponent(message)}`);
  }

  revalidatePath(path);
  revalidatePath(`/content-plans/${planId}`);
  revalidatePath("/");
  redirect(path);
}

async function regenerateVisualBriefAction(formData: FormData) {
  "use server";
  const planId = String(formData.get("planId"));
  const itemId = String(formData.get("itemId"));
  const path = `/content-plans/${planId}/items/${itemId}`;

  try {
    await postJson(`/content-plans/${planId}/items/${itemId}/regenerate-visual-brief`, {});
  } catch (error) {
    const message = error instanceof Error ? error.message : "Не удалось обновить промпт для иллюстрации.";
    redirect(`${path}?illustrationError=${encodeURIComponent(message)}`);
  }

  revalidatePath(path);
  redirect(path);
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
  revalidatePath(`/content-plans/${planId}`);
  revalidatePath("/");
}

async function saveDraftAction(formData: FormData) {
  "use server";
  const planId = String(formData.get("planId"));
  const itemId = String(formData.get("itemId"));
  const path = `/content-plans/${planId}/items/${itemId}`;
  const draftTitle = normalizeEditorialText(String(formData.get("draftTitle") || ""));
  const draftMarkdown = normalizeEditorialText(String(formData.get("draftMarkdown") || ""));
  const regenNote = String(formData.get("regenNote") || "").trim();

  const current = await fetchJson<ContentPlanItemDetail | null>(`/content-plans/${planId}/items/${itemId}`, null);
  if (!current) {
    throw new Error("Content plan item not found");
  }

  const researchData =
    current.research_data && typeof current.research_data === "object" ? { ...current.research_data } : {};
  const currentPayload =
    researchData.generation_payload && typeof researchData.generation_payload === "object"
      ? { ...(researchData.generation_payload as Record<string, unknown>) }
      : {};

  researchData.regen_note = regenNote;
  researchData.generation_payload = {
    ...currentPayload,
    draft_title: draftTitle,
    draft_markdown: draftMarkdown,
  };

  await patchJson(`/content-plans/${planId}/items/${itemId}`, {
    title: draftTitle || current.title,
    status: "draft",
    research_data: researchData,
  });

  revalidatePath(path);
  revalidatePath(`/content-plans/${planId}`);
  revalidatePath("/");
  redirect(path);
}

async function updateScheduleAction(formData: FormData) {
  "use server";
  const planId = String(formData.get("planId"));
  const itemId = String(formData.get("itemId"));
  const path = `/content-plans/${planId}/items/${itemId}`;
  const scheduledAt = normalizeScheduledAtInput(String(formData.get("scheduledAt") || ""));

  await patchJson(`/content-plans/${planId}/items/${itemId}`, {
    scheduled_at: scheduledAt,
  });

  revalidatePath(path);
  revalidatePath(`/content-plans/${planId}`);
  revalidatePath("/");
  redirect(path);
}

async function clearScheduleAction(formData: FormData) {
  "use server";
  const planId = String(formData.get("planId"));
  const itemId = String(formData.get("itemId"));
  const path = `/content-plans/${planId}/items/${itemId}`;

  await patchJson(`/content-plans/${planId}/items/${itemId}`, {
    scheduled_at: null,
  });

  revalidatePath(path);
  revalidatePath(`/content-plans/${planId}`);
  revalidatePath("/");
  redirect(path);
}

async function uploadIllustrationAction(formData: FormData) {
  "use server";
  const planId = String(formData.get("planId"));
  const itemId = String(formData.get("itemId"));
  const path = `/content-plans/${planId}/items/${itemId}`;
  const image = formData.get("image");

  if (!(image instanceof File) || image.size === 0) {
    redirect(`${path}?illustrationError=${encodeURIComponent("Сначала выберите файл изображения.")}`);
  }

  const uploadData = new FormData();
  uploadData.set("image", image);

  const response = await fetch(`${apiBaseUrl}/content-plans/${planId}/items/${itemId}/upload-illustration`, {
    method: "POST",
    body: uploadData,
    cache: "no-store",
  });

  if (!response.ok) {
    let message = "Не удалось загрузить изображение.";
    try {
      const payload = (await response.json()) as { detail?: unknown };
      if (typeof payload?.detail === "string" && payload.detail.trim()) {
        message = payload.detail.trim();
      }
    } catch {
      // ignore
    }
    redirect(`${path}?illustrationError=${encodeURIComponent(message)}`);
  }

  revalidatePath(path);
  revalidatePath(`/content-plans/${planId}`);
  revalidatePath("/");
  redirect(path);
}

export default async function ContentPlanItemPage({
  params,
  searchParams,
}: {
  params: Promise<{ planId: string; itemId: string }>;
  searchParams: Promise<{ publishError?: string; illustrationError?: string }>;
}) {
  const { planId, itemId } = await params;
  const { publishError, illustrationError } = await searchParams;
  const item = await fetchJson<ContentPlanItemDetail | null>(`/content-plans/${planId}/items/${itemId}`, null);

  if (!item) {
    return (
      <header className="page-header">
        <div>
          <h1>Тема не найдена</h1>
          <p className="lead">Не удалось загрузить данные элемента контент-плана.</p>
        </div>
      </header>
    );
  }

  const actions: string[] = [];
  const reviewNotes: string[] = [];
  const generationPayload: Record<string, unknown> | null = null;
  const channelTargets = Array.isArray(item.research_data?.channel_targets)
    ? (item.research_data.channel_targets as string[])
    : [];
  const assetBrief = typeof item.research_data?.asset_brief === "string" ? item.research_data.asset_brief : "";
  const channelAdaptations =
    item.channel_adaptations && typeof item.channel_adaptations === "object" ? item.channel_adaptations : {};
  const generatedImage =
    typeof item.research_data?.generated_image === "object" && item.research_data?.generated_image
      ? (item.research_data.generated_image as GeneratedImage)
      : null;
  const generatedImageUrl = generatedImage?.url
    ? `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api"}`.replace(/\/api$/, "") + generatedImage.url
    : null;
  const hasMasterDraft = Boolean(item.generated_draft_markdown);
  const isFallbackDraft = item.generation_mode === "fallback_generated";
  const savedRegenNote = typeof item.research_data?.regen_note === "string" ? item.research_data.regen_note : "";
  const canGenerate = item.status === "planned" || item.status === "draft" || item.status === "failed";

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">
            <Link href={`/content-plans/${planId}`} className="item-link" style={{ marginRight: "8px" }}>
              План
            </Link>
            / Тема #{item.order + 1}
          </p>
          <h1>{item.generated_draft_title || item.title}</h1>
          <p className="lead" style={{ marginTop: "12px" }}>
            Здесь собирается готовый материал для Telegram: пост, иллюстрация и при необходимости адаптации под другие
            каналы.
          </p>
          <p className="lead" style={{ marginTop: "12px", display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
            <span className={getBadgeClass(item.status)}>{getStatusLabel(item.status)}</span>
            <span>{item.article_type}</span>
            <span className="badge badge-accent">{item.cta_type} CTA</span>
            <span className="badge badge-outline">{formatGenerationMode(item.generation_mode)}</span>
            {item.scheduled_at ? <span className="badge badge-outline">План: {new Date(item.scheduled_at).toLocaleString("ru-RU")}</span> : null}
            {item.published_at ? <span className="badge badge-success">Опубликовано: {new Date(item.published_at).toLocaleString("ru-RU")}</span> : null}
          </p>
        </div>
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
          {false ? (
            <form action={updateStatusAction}>
              <input type="hidden" name="planId" value={planId} />
              <input type="hidden" name="itemId" value={itemId} />
              <input type="hidden" name="status" value="review-ready" />
              <SubmitButton className="btn" pendingLabel="Переводим на проверку...">
                На проверку
              </SubmitButton>
            </form>
          ) : null}
          {false ? (
            <form action={publishItemAction}>
              <input type="hidden" name="planId" value={planId} />
              <input type="hidden" name="itemId" value={itemId} />
              <SubmitButton className="btn btn-primary" pendingLabel="Публикуем в канал...">
                Запостить
              </SubmitButton>
            </form>
          ) : null}
          {hasMasterDraft ? (
            <form action={publishItemAction}>
              <input type="hidden" name="planId" value={planId} />
              <input type="hidden" name="itemId" value={itemId} />
              <SubmitButton className="btn btn-primary" pendingLabel="Публикуем в канал...">
                Опубликовать сейчас
              </SubmitButton>
            </form>
          ) : null}
          {item.status !== "archived" ? (
            <form action={updateStatusAction}>
              <input type="hidden" name="planId" value={planId} />
              <input type="hidden" name="itemId" value={itemId} />
              <input type="hidden" name="status" value="archived" />
              <SubmitButton className="btn" pendingLabel="\u041f\u0435\u0440\u0435\u043d\u043e\u0441\u0438\u043c \u0432 \u0430\u0440\u0445\u0438\u0432...">
                {"\u0412 \u0430\u0440\u0445\u0438\u0432"}
              </SubmitButton>
            </form>
          ) : (
            <form action={updateStatusAction}>
              <input type="hidden" name="planId" value={planId} />
              <input type="hidden" name="itemId" value={itemId} />
              <input type="hidden" name="status" value="draft" />
              <SubmitButton className="btn" pendingLabel="\u0412\u043e\u0437\u0432\u0440\u0430\u0449\u0430\u0435\u043c \u0432 \u0440\u0430\u0431\u043e\u0442\u0443...">
                {"\u0412\u0435\u0440\u043d\u0443\u0442\u044c \u0438\u0437 \u0430\u0440\u0445\u0438\u0432\u0430"}
              </SubmitButton>
            </form>
          )}
        </div>
      </header>

      {publishError ? (
        <article
          className="panel"
          style={{
            borderColor: "rgba(229, 108, 96, 0.35)",
            background: "rgba(229, 108, 96, 0.08)",
            marginBottom: "24px",
          }}
        >
          <div className="panel-header">
            <div>
              <span className="panel-kicker">Публикация не выполнена</span>
              <h2 className="panel-title" style={{ fontSize: "1.05rem" }}>
                {publishError}
              </h2>
            </div>
          </div>
        </article>
      ) : null}

      {illustrationError ? (
        <article
          className="panel"
          style={{
            borderColor: "rgba(229, 108, 96, 0.35)",
            background: "rgba(229, 108, 96, 0.08)",
            marginBottom: "24px",
          }}
        >
          <div className="panel-header">
            <div>
              <span className="panel-kicker">Иллюстрация не обновлена</span>
              <h2 className="panel-title" style={{ fontSize: "1.05rem" }}>
                {illustrationError}
              </h2>
            </div>
          </div>
        </article>
      ) : null}

      <section className="editor-layout">
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {isFallbackDraft ? (
            <article className="panel" style={{ borderColor: "var(--warning)" }}>
              <div className="panel-header">
                <span className="panel-kicker">Нужна доработка</span>
                <h2 className="panel-title">Черновик создан в fallback-режиме</h2>
              </div>
              <p style={{ margin: 0, color: "var(--muted)" }}>
                Это запасной вариант генерации. Такой текст обычно стоит перегенерировать через основную модель или
                быстро довести вручную перед публикацией.
              </p>
            </article>
          ) : null}

          <article className="panel">
            <div className="panel-header" style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "12px" }}>
              <div>
                <span className="panel-kicker">Визуал</span>
                <h2 className="panel-title">Иллюстрация</h2>
              </div>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                <form action={regenerateVisualBriefAction}>
                  <input type="hidden" name="planId" value={planId} />
                  <input type="hidden" name="itemId" value={itemId} />
                  <SubmitButton className="btn btn-ghost" pendingLabel="Обновляем промпт...">
                    Обновить промпт
                  </SubmitButton>
                </form>
                <form action={generateIllustrationAction}>
                  <input type="hidden" name="planId" value={planId} />
                  <input type="hidden" name="itemId" value={itemId} />
                  <SubmitButton className="btn" pendingLabel="Генерируем иллюстрацию...">
                    {generatedImageUrl ? "Перегенерировать иллюстрацию" : "Сгенерировать иллюстрацию"}
                  </SubmitButton>
                </form>
              </div>
            </div>

            {generatedImageUrl ? (
              <div style={{ display: "grid", gap: "16px" }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "center",
                    padding: "12px",
                    borderRadius: "18px",
                    border: "1px solid var(--border)",
                    background: "rgba(255,255,255,0.02)",
                  }}
                >
                  <img
                    src={generatedImageUrl}
                    alt={`Иллюстрация для темы ${item.title}`}
                    style={{
                      width: "100%",
                      maxWidth: "360px",
                      maxHeight: "360px",
                      borderRadius: "16px",
                      border: "1px solid var(--border)",
                      objectFit: "cover",
                      background: "rgba(255,255,255,0.03)",
                    }}
                  />
                </div>
                <details
                  style={{
                    background: "rgba(255,255,255,0.02)",
                    border: "1px solid var(--border)",
                    borderRadius: "14px",
                    padding: "14px 16px",
                  }}
                >
                  <summary style={{ cursor: "pointer", fontWeight: 600 }}>Показать prompt для иллюстрации</summary>
                  {generatedImage?.prompt ? (
                    <div className="preview-box" style={{ marginTop: "16px" }}>
                      <pre>{generatedImage.prompt}</pre>
                    </div>
                  ) : null}
                </details>
                <form action={uploadIllustrationAction} style={{ display: "grid", gap: "12px" }}>
                  <input type="hidden" name="planId" value={planId} />
                  <input type="hidden" name="itemId" value={itemId} />
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Заменить своим изображением</label>
                    <input type="file" name="image" className="form-input" accept="image/png,image/jpeg,image/webp" />
                  </div>
                  <div style={{ display: "flex", justifyContent: "flex-end" }}>
                    <SubmitButton className="btn" pendingLabel="Загружаем изображение...">
                      Загрузить своё изображение
                    </SubmitButton>
                  </div>
                </form>
              </div>
            ) : (
              <div className="empty-state" style={{ display: "grid", gap: "16px" }}>
                <strong>Иллюстрация пока не создана</strong>
                <p>После запуска генерации готовый визуал появится здесь и не будет перекрывать сам пост.</p>
                <form action={uploadIllustrationAction} style={{ display: "grid", gap: "12px", width: "100%", maxWidth: "420px" }}>
                  <input type="hidden" name="planId" value={planId} />
                  <input type="hidden" name="itemId" value={itemId} />
                  <div className="form-group" style={{ marginBottom: 0, textAlign: "left" }}>
                    <label className="form-label">Или загрузите своё изображение</label>
                    <input type="file" name="image" className="form-input" accept="image/png,image/jpeg,image/webp" />
                  </div>
                  <div style={{ display: "flex", justifyContent: "center" }}>
                    <SubmitButton className="btn" pendingLabel="Загружаем изображение...">
                      Загрузить своё изображение
                    </SubmitButton>
                  </div>
                </form>
              </div>
            )}
          </article>

          <article className="panel">
            <div className="panel-header" style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "12px" }}>
              <div>
                <span className="panel-kicker">Основной материал</span>
                <h2 className="panel-title">Telegram-пост</h2>
              </div>
              {canGenerate ? (
                <form action={startGenerationAction}>
                  <input type="hidden" name="planId" value={planId} />
                  <input type="hidden" name="itemId" value={itemId} />
                  <SubmitButton
                    className="btn btn-primary"
                    pendingLabel={item.status === "draft" ? "Перегенерируем пост..." : "Генерируем пост..."}
                  >
                    {item.status === "draft" ? "Перегенерировать пост" : "Сгенерировать пост"}
                  </SubmitButton>
                </form>
              ) : null}
            </div>

            {(item.generated_summary || item.generated_hook || item.generated_cta) ? (
              <div
                style={{
                  display: "grid",
                  gap: "12px",
                  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                  marginBottom: "20px",
                }}
              >
                {item.generated_hook ? (
                  <div className="panel" style={{ padding: "16px" }}>
                    <div className="panel-kicker">Хук</div>
                    <p style={{ margin: "8px 0 0", whiteSpace: "pre-wrap" }}>{item.generated_hook}</p>
                  </div>
                ) : null}
                {item.generated_summary ? (
                  <div className="panel" style={{ padding: "16px" }}>
                    <div className="panel-kicker">Коротко о сути</div>
                    <p style={{ margin: "8px 0 0", whiteSpace: "pre-wrap" }}>{item.generated_summary}</p>
                  </div>
                ) : null}
                {item.generated_cta ? (
                  <div className="panel" style={{ padding: "16px" }}>
                    <div className="panel-kicker">CTA</div>
                    <p style={{ margin: "8px 0 0", whiteSpace: "pre-wrap" }}>{item.generated_cta}</p>
                  </div>
                ) : null}
              </div>
            ) : null}

            {hasMasterDraft ? (
              <form action={saveDraftAction} style={{ display: "grid", gap: "16px" }}>
                <input type="hidden" name="planId" value={planId} />
                <input type="hidden" name="itemId" value={itemId} />
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Заголовок</label>
                  <input name="draftTitle" className="form-input" defaultValue={item.generated_draft_title || item.title} />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Текст поста</label>
                  <textarea
                    name="draftMarkdown"
                    className="form-input"
                    rows={18}
                    defaultValue={item.generated_draft_markdown || ""}
                    style={{ minHeight: "420px", resize: "vertical" }}
                  />
                </div>
                <p style={{ margin: 0, color: "var(--muted)", fontSize: "0.92rem" }}>
                  Длинные тире при сохранении автоматически заменяются на короткие, чтобы текст выглядел живее и менее
                  шаблонно.
                </p>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Комментарий для перегенерации</label>
                  <textarea
                    name="regenNote"
                    className="form-input"
                    rows={3}
                    defaultValue={savedRegenNote}
                    placeholder="Что изменить в следующей версии? Например: сделать короче, добавить конкретный пример, убрать CTA..."
                    style={{ resize: "vertical" }}
                  />
                </div>
                <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px", flexWrap: "wrap" }}>
                  <button type="submit" formAction={regenerateDraftAction} className="btn">
                    Перегенерировать текст
                  </button>
                  <SubmitButton className="btn btn-primary" pendingLabel="Сохраняем правки...">
                    Сохранить правки
                  </SubmitButton>
                </div>
              </form>
            ) : (
              <div className="empty-state">
                <strong>Текст пока не создан</strong>
                <p>После запуска генерации здесь появится готовый пост, который можно будет сразу поправить вручную.</p>
              </div>
            )}
          </article>

          {false ? <article className="panel">
            <div className="panel-header">
              <span className="panel-kicker">Следующие шаги</span>
              <h2 className="panel-title">Что можно сделать дальше</h2>
            </div>
            <ul style={{ margin: 0, paddingLeft: "20px", color: "var(--muted)", display: "grid", gap: "8px" }}>
              <li>Если пост всё ещё длинноват, перегенерируйте его: промпт уже ориентирован именно на Telegram.</li>
              <li>Если визуал не попал в задачу, перегенерируйте иллюстрацию отдельно, не трогая текст.</li>
              <li>Когда текст и картинка устраивают, переводите материал в статус «На проверку».</li>
            </ul>
          </article> : null}

          <JobPolling planId={planId} itemId={itemId} initialStatus={item.status} />
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          <article className="panel">
            <div className="panel-header" style={{ marginBottom: "12px" }}>
              <span className="panel-kicker">Бриф и стратегия</span>
            </div>
            <div className="panel-header" style={{ marginBottom: "12px" }}>
              <span className="panel-kicker">Публикация</span>
              <h2 className="panel-title">Дата и время выхода</h2>
            </div>
            <form action={updateScheduleAction} style={{ display: "grid", gap: "14px", marginBottom: "24px" }}>
              <input type="hidden" name="planId" value={planId} />
              <input type="hidden" name="itemId" value={itemId} />
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Запланировать публикацию</label>
                <input
                  type="datetime-local"
                  name="scheduledAt"
                  className="form-input"
                  defaultValue={toDateTimeInputValue(item.scheduled_at)}
                />
              </div>
              <p style={{ margin: 0, color: "var(--muted)", fontSize: "0.9rem" }}>
                Если дату поменять вручную, календарь плана сразу обновится.
              </p>
              <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                <SubmitButton className="btn" pendingLabel="Сохраняем дату...">
                  Сохранить дату
                </SubmitButton>
                <button type="submit" formAction={clearScheduleAction} className="btn">
                  Очистить дату
                </button>
              </div>
            </form>
            <div className="key-value-stack">
              <div className="kv-pair">
                <span className="kv-label">Тема</span>
                <span className="kv-val">{item.title}</span>
              </div>
              <div className="kv-pair">
                <span className="kv-label">Угол подачи</span>
                <span className="kv-val">{item.angle || "Не указан"}</span>
              </div>
              <div className="kv-pair">
                <span className="kv-label">Ключевые слова</span>
                <span className="kv-val">
                  {item.target_keywords.length > 0 ? (
                    <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginTop: "4px" }}>
                      {item.target_keywords.map((keyword) => (
                        <span key={keyword} className="badge badge-outline">
                          {keyword}
                        </span>
                      ))}
                    </div>
                  ) : (
                    "Не указаны"
                  )}
                </span>
              </div>
              <div className="kv-pair">
                <span className="kv-label">Каналы</span>
                <span className="kv-val">
                  {channelTargets.length > 0 ? (
                    <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginTop: "4px" }}>
                      {channelTargets.map((target) => (
                        <span key={target} className="badge badge-outline">
                          {prettifyChannel(target)}
                        </span>
                      ))}
                    </div>
                  ) : (
                    "Не указаны"
                  )}
                </span>
              </div>
              {assetBrief ? (
                <div className="kv-pair">
                  <span className="kv-label">Визуальный бриф</span>
                  <span className="kv-val">{assetBrief}</span>
                </div>
              ) : null}
            </div>
          </article>

          {Object.keys(channelAdaptations).length > 0 ? (
            <article className="panel">
              <div className="panel-header" style={{ marginBottom: "12px" }}>
                <span className="panel-kicker">Адаптации по каналам</span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {Object.entries(channelAdaptations).map(([channel, adaptation]) => (
                  <div
                    key={channel}
                    style={{
                      padding: "12px",
                      border: "1px solid var(--border)",
                      borderRadius: "12px",
                      background: "rgba(255,255,255,0.02)",
                    }}
                  >
                    <div style={{ display: "flex", gap: "8px", alignItems: "center", marginBottom: "8px", flexWrap: "wrap" }}>
                      <strong>{prettifyChannel(channel)}</strong>
                      {adaptation.format ? <span className="badge badge-outline">{adaptation.format}</span> : null}
                    </div>
                    {adaptation.content_markdown ? (
                      <pre style={{ whiteSpace: "pre-wrap", margin: 0 }}>{adaptation.content_markdown}</pre>
                    ) : (
                      <p style={{ margin: 0, color: "var(--muted)" }}>Текст адаптации пока не создан.</p>
                    )}
                    {adaptation.asset_brief ? (
                      <p style={{ color: "var(--muted)", marginTop: "8px", marginBottom: 0 }}>{adaptation.asset_brief}</p>
                    ) : null}
                  </div>
                ))}
              </div>
            </article>
          ) : null}

          {false ? (
            <article className="panel">
              <div className="panel-header" style={{ marginBottom: "12px" }}>
                <span className="panel-kicker">Заметки редактора</span>
              </div>
              <ul style={{ listStylePosition: "inside", padding: 0, margin: 0, color: "var(--text)" }}>
                {reviewNotes.map((note, index) => (
                  <li key={index} style={{ marginBottom: "8px", fontSize: "0.9rem" }}>
                    {note}
                  </li>
                ))}
              </ul>
            </article>
          ) : null}

          {false ? (
            <details style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "16px", padding: "16px" }}>
              <summary style={{ cursor: "pointer", fontWeight: "600", color: "var(--muted)", outline: "none" }}>
                Данные для разработчиков
              </summary>
              <div className="preview-box" style={{ marginTop: "16px" }}>
                <pre>{JSON.stringify(generationPayload, null, 2)}</pre>
              </div>
            </details>
          ) : null}

          {false ? <div style={{ marginTop: "12px", display: "flex", flexDirection: "column", gap: "8px" }}>
            {actions.map((action) => {
              if (action === "generate" || action === "review-ready" || action === "published") return null;
              return (
                <form action={updateStatusAction} key={action} style={{ width: "100%" }}>
                  <input type="hidden" name="planId" value={planId} />
                  <input type="hidden" name="itemId" value={itemId} />
                  <input type="hidden" name="status" value={action} />
                  <SubmitButton className="btn" style={{ width: "100%" }} pendingLabel={`Переводим в ${statusLabel(action).toLowerCase()}...`}>
                    Перевести в {statusLabel(action)}
                  </SubmitButton>
                </form>
              );
            })}
          </div> : null}
        </div>
      </section>
    </>
  );
}
