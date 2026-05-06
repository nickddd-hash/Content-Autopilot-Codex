import Link from "next/link";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import SubmitButton from "@/components/SubmitButton";
import { deleteJson, fetchJson, postJson } from "@/lib/api";

import PlanMixConfigurator from "./PlanMixConfigurator";
import PlanJobPolling from "./PlanJobPolling";
import QuickPostModal from "./QuickPostModal";

type ContentPlanItem = {
  id: string;
  order: number;
  title: string;
  generated_draft_title?: string | null;
  angle: string | null;
  status: string;
  article_type: string;
  cta_type: string;
  target_keywords: string[];
  scheduled_at?: string | null;
  published_at?: string | null;
};

type ContentPlan = {
  id: string;
  product_id: string;
  month: string;
  theme: string | null;
  status: string;
  settings_json?: {
    content_mix?: {
      practical?: number;
      educational?: number;
      news?: number;
      opinion?: number;
      critical?: number;
    };
    needs_reschedule?: boolean;
    reschedule_reason?: string | null;
  };
  items: ContentPlanItem[];
};

type ProductSummary = {
  id: string;
  primary_channels: string[];
};

type PlanJob = {
  id: string;
  job_type: string;
  status: string;
  error_message?: string | null;
};

const CALENDAR_WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

function buildDayKey(year: number, monthIndex: number, day: number) {
  return `${year}-${String(monthIndex + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function buildMonthCalendarFromParts(year: number, monthIndex: number) {
  const firstDay = new Date(Date.UTC(year, monthIndex, 1));
  const daysInMonth = new Date(Date.UTC(year, monthIndex + 1, 0)).getUTCDate();
  const leadingEmpty = (firstDay.getUTCDay() + 6) % 7;
  const cells: Array<{ day: number; key: string } | null> = [];

  for (let index = 0; index < leadingEmpty; index += 1) {
    cells.push(null);
  }

  for (let day = 1; day <= daysInMonth; day += 1) {
    cells.push({ day, key: buildDayKey(year, monthIndex, day) });
  }

  return { year, monthIndex, cells };
}

function addMonths(date: Date, amount: number) {
  return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + amount, 1));
}

function formatMonthLabel(year: number, monthIndex: number) {
  return new Intl.DateTimeFormat("ru-RU", {
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(Date.UTC(year, monthIndex, 1)));
}

function formatDayLabel(dayKey: string) {
  const date = new Date(`${dayKey}T00:00:00Z`);
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
    weekday: "long",
    timeZone: "UTC",
  }).format(date);
}

function formatScheduledLabel(value?: string | null) {
  if (!value) return "";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function hasBrokenDisplayText(value?: string | null) {
  if (!value) return false;
  const trimmed = value.trim();
  if (!trimmed) return false;
  if (trimmed.includes("�")) return true;
  const questionMarkCount = [...trimmed].filter((symbol) => symbol === "?").length;
  return questionMarkCount >= 3 && questionMarkCount / trimmed.length > 0.08;
}

function getItemDisplayTitle(item: ContentPlanItem) {
  const fallbackTitle = item.generated_draft_title?.trim();
  if (hasBrokenDisplayText(item.title) && fallbackTitle && !hasBrokenDisplayText(fallbackTitle)) {
    return fallbackTitle;
  }
  return item.title;
}

function getDominantDirection(
  contentMix?: ContentPlan["settings_json"] extends infer T ? T extends { content_mix?: infer U } ? U : never : never,
) {
  const entries = Object.entries({
    practical: contentMix?.practical ?? 60,
    educational: contentMix?.educational ?? 20,
    news: contentMix?.news ?? 10,
    opinion: contentMix?.opinion ?? 5,
    critical: contentMix?.critical ?? 5,
  }) as Array<["practical" | "educational" | "news" | "opinion" | "critical", number]>;

  return entries.sort((left, right) => right[1] - left[1])[0]?.[0] ?? "educational";
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    draft: "Черновик",
    planned: "Запланировано",
    "review-ready": "Пост готов",
    published: "Опубликовано",
    failed: "Ошибка",
    active: "Активен",
    running: "В работе",
    pending: "В очереди",
    completed: "Завершено",
  };

  return labels[status] || status;
}

function getBadgeClass(status: string) {
  const normalized = status.toLowerCase();
  if (["published", "completed"].includes(normalized)) return "badge badge-success";
  if (["draft", "planned"].includes(normalized)) return "badge badge-outline";
  if (["failed", "error"].includes(normalized)) return "badge badge-danger";
  if (["running", "in_progress"].includes(normalized)) return "badge badge-warning";
  if (["review-ready"].includes(normalized)) return "badge badge-info";
  return "badge badge-info";
}

function getStatusHintClean(status: string) {
  if (status === "planned") return "Тема уже в плане. Можно сразу собрать пост и иллюстрацию.";
  if (status === "draft") return "Материал уже собран. Откройте пост, поправьте текст или публикуйте сразу.";
  if (status === "review-ready") return "Пост готов к публикации и ждёт своего времени в календаре.";
  if (status === "published") return "Материал уже опубликован и доступен для просмотра в истории плана.";
  return "Откройте материал, чтобы посмотреть и отредактировать его.";
}

function shouldShowGenerateButton(status: string) {
  return ["planned"].includes(status);
}

function formatArticleType(value: string) {
  const labels: Record<string, string> = {
    practical: "practical",
    educational: "educational",
    news: "news",
    opinion: "opinion",
    critical: "critical",
    checklist: "checklist",
  };

  return labels[value] || value;
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

  await postJson(`/content-plans/${planId}/run-pipeline`, {
    generate_items: true,
    theme: payload.theme ?? null,
    num_items: payload.num_items ?? null,
  });

  revalidatePath(`/content-plans/${planId}`);
  revalidatePath("/");
  redirect(`/content-plans/${planId}`);
}

async function generateItemBundleAction(formData: FormData) {
  "use server";
  const planId = String(formData.get("planId"));
  const itemId = String(formData.get("itemId"));

  await postJson(`/content-plans/${planId}/items/${itemId}/generate`, {});
  await postJson(`/content-plans/${planId}/items/${itemId}/generate-illustration`, {});

  revalidatePath(`/content-plans/${planId}`);
  revalidatePath(`/content-plans/${planId}/items/${itemId}`);
  revalidatePath("/");
  redirect(`/content-plans/${planId}?highlight=${itemId}#item-${itemId}`);
}

async function buildPlanMaterialsAction(formData: FormData) {
  "use server";
  const planId = String(formData.get("planId"));

  await postJson(`/content-plans/${planId}/run-pipeline`, {
    generate_items: false,
  });
  revalidatePath(`/content-plans/${planId}`);
  revalidatePath("/");
  redirect(`/content-plans/${planId}`);
}

async function moveStatusAction(formData: FormData) {
  "use server";
  const planId = String(formData.get("planId"));
  const itemId = String(formData.get("itemId"));
  const status = String(formData.get("status"));

  await postJson(`/content-plans/${planId}/items/${itemId}/status`, { status });
  revalidatePath(`/content-plans/${planId}`);
  revalidatePath(`/content-plans/${planId}/items/${itemId}`);
}

async function deletePlanAction(formData: FormData) {
  "use server";
  const planId = String(formData.get("planId"));
  const productId = String(formData.get("productId"));

  await deleteJson(`/content-plans/${planId}`);
  revalidatePath("/");
  revalidatePath(`/products/${productId}`);
  redirect(`/products/${productId}`);
}

export default async function ContentPlanPage({
  params,
  searchParams,
}: {
  params: Promise<{ planId: string }>;
  searchParams: Promise<{ highlight?: string; day?: string }>;
}) {
  const { planId } = await params;
  const { highlight, day } = await searchParams;
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

  const highlightId = highlight || "";
  const product = await fetchJson<ProductSummary | null>(`/products/${plan.product_id}`, null);
  const latestJob = await fetchJson<PlanJob | null>(`/content-plans/${plan.id}/latest-job`, null);
  const productChannels = product?.primary_channels ?? [];
  const contentMix = {
    practical: plan.settings_json?.content_mix?.practical ?? 60,
    educational: plan.settings_json?.content_mix?.educational ?? 20,
    news: plan.settings_json?.content_mix?.news ?? 10,
    opinion: plan.settings_json?.content_mix?.opinion ?? 5,
    critical: plan.settings_json?.content_mix?.critical ?? 5,
  };
  const dominantDirection = getDominantDirection(plan.settings_json?.content_mix);
  const visibleItems = plan.items.filter((item) => item.status !== "archived");
  const scheduledItems = visibleItems.filter((item) => Boolean(item.scheduled_at));
  const scheduledItemsByDay = new Map<string, ContentPlanItem[]>();
  for (const item of scheduledItems) {
    const dayKey = String(item.scheduled_at).slice(0, 10);
    const currentItems = scheduledItemsByDay.get(dayKey) ?? [];
    currentItems.push(item);
    scheduledItemsByDay.set(dayKey, currentItems);
  }
  const today = new Date();
  const currentMonthDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1));
  const nextMonthDate = addMonths(currentMonthDate, 1);
  const calendars = [
    buildMonthCalendarFromParts(currentMonthDate.getUTCFullYear(), currentMonthDate.getUTCMonth()),
    buildMonthCalendarFromParts(nextMonthDate.getUTCFullYear(), nextMonthDate.getUTCMonth()),
  ];
  const todayKey = buildDayKey(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate());
  const availableDayKeys = [...scheduledItemsByDay.keys()].sort();
  const selectedDay =
    day ||
    (scheduledItemsByDay.has(todayKey) ? todayKey : availableDayKeys[0] ?? todayKey);
  const selectedDayItems = selectedDay ? scheduledItemsByDay.get(selectedDay) ?? [] : [];

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">Контент-план: {plan.month}</p>
          <h1>{plan.theme || "План без фиксированной темы"}</h1>
          <p className="lead" style={{ marginTop: "12px", display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
            <span className={getBadgeClass(plan.status)}>{statusLabel(plan.status)}</span>
            <span>Темы: {plan.items.length}</span>
          </p>
        </div>
      </header>

      <section className="panel-grid" style={{ gridTemplateColumns: "1fr" }}>
        <PlanJobPolling planId={plan.id} initialJob={latestJob} />

        <article className="panel">
          <div className="panel-header" style={{ alignItems: "flex-start", gap: "20px" }}>
            <div style={{ flex: 1 }}>
              <span className="panel-kicker">Планирование</span>
              <h2 className="panel-title">Генерация тем</h2>
              <p className="form-hint" style={{ marginTop: "10px" }}>
                Можно оставить тему пустой, чтобы система сама собрала идеи по контексту продукта. Или задать спецтему и
                точное количество постов для отдельного блока.
              </p>
            </div>
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", justifyContent: "flex-end" }}>
              <PlanMixConfigurator planId={plan.id} initialMix={contentMix} />
              <QuickPostModal planId={plan.id} initialDirection={dominantDirection} channels={productChannels} />
              <form action={buildPlanMaterialsAction}>
                <input type="hidden" name="planId" value={plan.id} />
                <SubmitButton className="btn btn-primary" pendingLabel="Собираем материалы...">
                  Собрать материалы
                </SubmitButton>
              </form>
              <Link href={`/products/${plan.product_id}`} className="btn">
                К продукту
              </Link>
              <Link href="/" className="btn">
                На дашборд
              </Link>
              <form action={deletePlanAction}>
                <input type="hidden" name="planId" value={plan.id} />
                <input type="hidden" name="productId" value={plan.product_id} />
                <SubmitButton className="btn" style={{ borderColor: "var(--danger)", color: "var(--danger)" }} pendingLabel="Удаляем план...">
                  Удалить план
                </SubmitButton>
              </form>
            </div>
          </div>

          <form action={generatePlanItemsAction} style={{ display: "grid", gap: "16px", gridTemplateColumns: "1fr 180px auto" }}>
            <input type="hidden" name="planId" value={plan.id} />
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Спецтема</label>
              <input
                type="text"
                name="themeOverride"
                className="form-input"
                placeholder="Например: идеи для Telegram о простом внедрении AI"
              />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Сколько постов</label>
              <input type="number" name="numItems" className="form-input" min={1} max={30} placeholder="Авто" defaultValue={plan.settings_json?.num_items_default ?? ""} />
            </div>
            <div style={{ display: "flex", alignItems: "end" }}>
              <SubmitButton className="btn btn-primary" pendingLabel="Генерируем темы...">
                Сгенерировать темы
              </SubmitButton>
            </div>
          </form>

          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginTop: "16px" }}>
            <span className="badge badge-outline">Practical {contentMix.practical}%</span>
            <span className="badge badge-outline">Educational {contentMix.educational}%</span>
            <span className="badge badge-outline">News {contentMix.news}%</span>
            <span className="badge badge-outline">Opinion {contentMix.opinion}%</span>
            <span className="badge badge-outline">Critical {contentMix.critical}%</span>
          </div>

          {highlightId ? (
            <div
              style={{
                marginTop: "16px",
                padding: "14px 16px",
                borderRadius: "14px",
                border: "1px solid rgba(255, 210, 110, 0.35)",
                background: "rgba(255, 210, 110, 0.08)",
                color: "var(--text)",
              }}
            >
              Новая тема подсвечена в списке ниже.
            </div>
          ) : null}
        </article>

        {plan.settings_json?.needs_reschedule ? (
          <article className="panel" style={{ borderColor: "rgba(255, 196, 107, 0.45)", background: "rgba(255, 196, 107, 0.08)" }}>
            <div className="panel-header">
              <div>
                <span className="panel-kicker">Расписание требует пересмотра</span>
                <h2 className="panel-title">Один из постов уже опубликован вручную раньше срока</h2>
              </div>
            </div>
            <p className="form-hint" style={{ marginTop: "10px" }}>
              Пересоберите материалы, чтобы контент-завод заново разложил оставшиеся публикации по календарю.
            </p>
          </article>
        ) : null}

        <article className="panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">Календарь</span>
              <h2 className="panel-title">План публикаций по дням</h2>
            </div>
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "320px minmax(0, 1fr)",
              gap: "24px",
              alignItems: "start",
            }}
          >
            <div style={{ display: "grid", gap: "18px" }}>
              {calendars.map((calendar) => (
                <div
                  key={`${calendar.year}-${calendar.monthIndex}`}
                  style={{
                    border: "1px solid var(--border)",
                    borderRadius: "18px",
                    padding: "16px",
                    background: "rgba(255,255,255,0.72)",
                  }}
                >
                  <div style={{ fontWeight: 700, marginBottom: "12px", textTransform: "capitalize" }}>
                    {formatMonthLabel(calendar.year, calendar.monthIndex)}
                  </div>
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(7, minmax(0, 1fr))",
                      gap: "6px",
                    }}
                  >
                    {CALENDAR_WEEKDAYS.map((weekday) => (
                      <div
                        key={`${calendar.year}-${calendar.monthIndex}-${weekday}`}
                        style={{
                          fontSize: "0.75rem",
                          color: "var(--muted)",
                          fontWeight: 600,
                          textAlign: "center",
                          paddingBottom: "4px",
                        }}
                      >
                        {weekday}
                      </div>
                    ))}

                    {calendar.cells.map((cell, index) => {
                      if (!cell) {
                        return <div key={`${calendar.year}-${calendar.monthIndex}-empty-${index}`} aria-hidden="true" />;
                      }

                      const dayItems = scheduledItemsByDay.get(cell.key) ?? [];
                      const isSelected = cell.key === selectedDay;
                      const isPastInCurrentMonth =
                        calendar.year === currentMonthDate.getUTCFullYear() &&
                        calendar.monthIndex === currentMonthDate.getUTCMonth() &&
                        cell.day < today.getUTCDate();

                      return (
                        <Link
                          key={cell.key}
                          href={`/content-plans/${plan.id}?day=${cell.key}`}
                          style={{
                            minHeight: "54px",
                            padding: "8px 6px",
                            borderRadius: "12px",
                            border: isSelected ? "1px solid rgba(176, 191, 119, 0.7)" : "1px solid var(--border)",
                            background: isSelected ? "rgba(176, 191, 119, 0.16)" : "rgba(255,255,255,0.92)",
                            textDecoration: "none",
                            color: "var(--text)",
                            display: "grid",
                            alignContent: "space-between",
                            justifyItems: "start",
                            opacity: isPastInCurrentMonth ? 0.42 : 1,
                          }}
                        >
                          <span style={{ fontWeight: 700, fontSize: "0.95rem" }}>{cell.day}</span>
                          <span style={{ fontSize: "0.72rem", color: dayItems.length ? "var(--text)" : "var(--muted)" }}>
                            {dayItems.length ? `${dayItems.length} пост` : ""}
                          </span>
                        </Link>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            <div
              style={{
                border: "1px solid var(--border)",
                borderRadius: "18px",
                padding: "18px 20px",
                background: "rgba(255,255,255,0.72)",
                minHeight: "100%",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", alignItems: "center", flexWrap: "wrap", marginBottom: "14px" }}>
                <div>
                  <div className="panel-kicker">Выбранный день</div>
                  <h3 style={{ margin: "6px 0 0", fontSize: "1.05rem" }}>{formatDayLabel(selectedDay)}</h3>
                </div>
                <span className="badge badge-outline">{selectedDayItems.length} в плане</span>
              </div>

              {selectedDayItems.length ? (
                <div className="list-container">
                  {selectedDayItems
                    .sort((left, right) => String(left.scheduled_at).localeCompare(String(right.scheduled_at)))
                    .map((item) => (
                      <div key={item.id} className="list-item compact-list-item">
                        <div style={{ minWidth: 0 }}>
                          <div className="list-item-sub">{formatScheduledLabel(item.scheduled_at)}</div>
                          <Link href={`/content-plans/${plan.id}/items/${item.id}`} className="list-item-title item-link" style={{ textDecoration: "none" }}>
                            {getItemDisplayTitle(item)}
                          </Link>
                        </div>
                        <span className={getBadgeClass(item.status)}>{statusLabel(item.status)}</span>
                      </div>
                    ))}
                </div>
              ) : (
                <div className="empty-state compact-empty-state">
                  <strong>На этот день постов нет</strong>
                </div>
              )}
            </div>
          </div>
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">Материалы</span>
              <h2 className="panel-title">Очередь контента</h2>
            </div>
          </div>

          <div className="list-container">
            {visibleItems.length > 0 ? (
              visibleItems.map((item) => {
                const isHighlighted = item.id === highlightId;

                return (
                  <div
                    key={item.id}
                    id={`item-${item.id}`}
                    className="list-item"
                    style={{
                      alignItems: "flex-start",
                      padding: "24px 0",
                      borderLeft: isHighlighted ? "3px solid rgba(255, 210, 110, 0.85)" : undefined,
                      paddingLeft: isHighlighted ? "16px" : undefined,
                      background: isHighlighted ? "rgba(255, 210, 110, 0.05)" : undefined,
                      borderRadius: isHighlighted ? "16px" : undefined,
                      scrollMarginTop: "120px",
                    }}
                  >
                    <div style={{ paddingRight: "40px", flex: 1 }}>
                      <span className="list-item-sub" style={{ display: "block", marginBottom: "8px" }}>
                        #{item.order + 1} · {formatArticleType(item.article_type)}
                      </span>
                      <Link
                        href={`/content-plans/${plan.id}/items/${item.id}`}
                        className="list-item-title item-link"
                        style={{ fontSize: "1.1rem", textDecoration: "none" }}
                      >
                        {getItemDisplayTitle(item)}
                      </Link>
                      <p style={{ color: "var(--muted)", margin: "8px 0", fontSize: "0.9rem", maxWidth: "800px" }}>
                        {item.angle || "Угол подачи пока не задан."}
                      </p>
                      <div style={{ display: "flex", gap: "8px", marginTop: "12px", flexWrap: "wrap" }}>
                        {isHighlighted ? <span className="badge badge-warning">Новое</span> : null}
                        {item.target_keywords.map((keyword) => (
                          <span key={keyword} className="badge badge-outline" style={{ fontSize: "0.7rem" }}>
                            {keyword}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "12px", minWidth: "250px" }}>
                      {item.status === "review-ready" ? (
                        <span
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "8px",
                            padding: "8px 14px",
                            borderRadius: "999px",
                            background: "rgba(112, 214, 130, 0.12)",
                            border: "1px solid rgba(112, 214, 130, 0.35)",
                            color: "#86f09a",
                            fontSize: "0.82rem",
                            fontWeight: 600,
                          }}
                        >
                          <span aria-hidden="true">✓</span>
                          <span>Пост готов</span>
                        </span>
                      ) : (
                        <span className={getBadgeClass(item.status)}>{statusLabel(item.status)}</span>
                      )}
                      <p style={{ margin: 0, color: "var(--muted)", fontSize: "0.85rem", textAlign: "right" }}>{getStatusHintClean(item.status)}</p>
                      {item.scheduled_at ? (
                        <p style={{ margin: 0, color: "var(--muted)", fontSize: "0.8rem", textAlign: "right" }}>
                          План: {new Date(item.scheduled_at).toLocaleString("ru-RU")}
                        </p>
                      ) : null}
                      {item.published_at ? (
                        <p style={{ margin: 0, color: "var(--muted)", fontSize: "0.8rem", textAlign: "right" }}>
                          Опубликовано: {new Date(item.published_at).toLocaleString("ru-RU")}
                        </p>
                      ) : null}
                      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", justifyContent: "flex-end" }}>
                        {shouldShowGenerateButton(item.status) ? (
                          <form action={generateItemBundleAction}>
                            <input type="hidden" name="planId" value={plan?.id ?? ""} />
                            <input type="hidden" name="itemId" value={item.id} />
                            <SubmitButton
                              className="btn btn-primary"
                              pendingLabel={item.status === "draft" ? "Перегенерируем пост и иллюстрацию..." : "Генерируем пост и иллюстрацию..."}
                            >
                              Генерация
                            </SubmitButton>
                          </form>
                        ) : null}
                        {false ? (
                          <form action={moveStatusAction}>
                            <input type="hidden" name="planId" value={plan?.id ?? ""} />
                            <input type="hidden" name="itemId" value={item.id} />
                            <input type="hidden" name="status" value="review-ready" />
                            <SubmitButton className="btn" pendingLabel="Отмечаем пост как готовый...">
                              Готово
                            </SubmitButton>
                          </form>
                        ) : null}
                        {item.status === "draft" || item.status === "review-ready" || item.status === "published" ? (
                          <Link href={`/content-plans/${plan.id}/items/${item.id}`} className="btn">
                            Открыть пост
                          </Link>
                        ) : null}
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="empty-state">
                <strong>В очереди пока пусто</strong>
                <p>Нажмите «Сгенерировать темы», чтобы собрать новый план и потом перейти к генерации материалов.</p>
              </div>
            )}
          </div>
        </article>
      </section>
    </>
  );
}
