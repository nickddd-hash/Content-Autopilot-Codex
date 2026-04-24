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

const CALENDAR_WEEKDAYS = ["РџРЅ", "Р’С‚", "РЎСЂ", "Р§С‚", "РџС‚", "РЎР±", "Р’СЃ"];

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

function getDominantDirection(
  contentMix?: ContentPlan["settings_json"] extends infer T ? T extends { content_mix?: infer U } ? U : never : never,
) {
  const entries = Object.entries({
    practical: contentMix?.practical ?? 40,
    educational: contentMix?.educational ?? 25,
    news: contentMix?.news ?? 15,
    opinion: contentMix?.opinion ?? 10,
    critical: contentMix?.critical ?? 10,
  }) as Array<["practical" | "educational" | "news" | "opinion" | "critical", number]>;

  return entries.sort((left, right) => right[1] - left[1])[0]?.[0] ?? "educational";
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    draft: "Р§РµСЂРЅРѕРІРёРє",
    planned: "Р—Р°РїР»Р°РЅРёСЂРѕРІР°РЅРѕ",
    "review-ready": "РџРѕСЃС‚ РіРѕС‚РѕРІ",
    published: "РћРїСѓР±Р»РёРєРѕРІР°РЅРѕ",
    failed: "РћС€РёР±РєР°",
    active: "РђРєС‚РёРІРµРЅ",
    running: "Р’ СЂР°Р±РѕС‚Рµ",
    pending: "Р’ РѕС‡РµСЂРµРґРё",
    completed: "Р—Р°РІРµСЂС€РµРЅРѕ",
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
  if (status === "planned") return "РўРµРјР° СѓР¶Рµ РІ РїР»Р°РЅРµ. РњРѕР¶РЅРѕ СЃСЂР°Р·Сѓ СЃРѕР±СЂР°С‚СЊ РїРѕСЃС‚ Рё РёР»Р»СЋСЃС‚СЂР°С†РёСЋ.";
  if (status === "draft") return "РњР°С‚РµСЂРёР°Р» СѓР¶Рµ СЃРѕР±СЂР°РЅ. РћС‚РєСЂРѕР№С‚Рµ РїРѕСЃС‚, РїРѕРїСЂР°РІСЊС‚Рµ С‚РµРєСЃС‚ РёР»Рё РїСѓР±Р»РёРєСѓР№С‚Рµ СЃСЂР°Р·Сѓ.";
  if (status === "review-ready") return "РџРѕСЃС‚ РіРѕС‚РѕРІ Рє РїСѓР±Р»РёРєР°С†РёРё Рё Р¶РґС‘С‚ СЃРІРѕРµРіРѕ РІСЂРµРјРµРЅРё РІ РєР°Р»РµРЅРґР°СЂРµ.";
  if (status === "published") return "РњР°С‚РµСЂРёР°Р» СѓР¶Рµ РѕРїСѓР±Р»РёРєРѕРІР°РЅ Рё РґРѕСЃС‚СѓРїРµРЅ РґР»СЏ РїСЂРѕСЃРјРѕС‚СЂР° РІ РёСЃС‚РѕСЂРёРё РїР»Р°РЅР°.";
  return "РћС‚РєСЂРѕР№С‚Рµ РјР°С‚РµСЂРёР°Р», С‡С‚РѕР±С‹ РїРѕСЃРјРѕС‚СЂРµС‚СЊ Рё РѕС‚СЂРµРґР°РєС‚РёСЂРѕРІР°С‚СЊ РµРіРѕ.";
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
          <h1>РџР»Р°РЅ РЅРµ РЅР°Р№РґРµРЅ</h1>
          <p className="lead">РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РіСЂСѓР·РёС‚СЊ РґР°РЅРЅС‹Рµ РєРѕРЅС‚РµРЅС‚-РїР»Р°РЅР°.</p>
        </div>
      </header>
    );
  }

  const highlightId = highlight || "";
  const product = await fetchJson<ProductSummary | null>(`/products/${plan.product_id}`, null);
  const latestJob = await fetchJson<PlanJob | null>(`/content-plans/${plan.id}/latest-job`, null);
  const productChannels = product?.primary_channels ?? [];
  const contentMix = {
    practical: plan.settings_json?.content_mix?.practical ?? 40,
    educational: plan.settings_json?.content_mix?.educational ?? 25,
    news: plan.settings_json?.content_mix?.news ?? 15,
    opinion: plan.settings_json?.content_mix?.opinion ?? 10,
    critical: plan.settings_json?.content_mix?.critical ?? 10,
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
          <p className="eyebrow">РљРѕРЅС‚РµРЅС‚-РїР»Р°РЅ: {plan.month}</p>
          <h1>{plan.theme || "РџР»Р°РЅ Р±РµР· С„РёРєСЃРёСЂРѕРІР°РЅРЅРѕР№ С‚РµРјС‹"}</h1>
          <p className="lead" style={{ marginTop: "12px", display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
            <span className={getBadgeClass(plan.status)}>{statusLabel(plan.status)}</span>
            <span>РўРµРјС‹: {plan.items.length}</span>
          </p>
        </div>
      </header>

      <section className="panel-grid" style={{ gridTemplateColumns: "1fr" }}>
        <PlanJobPolling planId={plan.id} initialJob={latestJob} />

        <article className="panel">
          <div className="panel-header" style={{ alignItems: "flex-start", gap: "20px" }}>
            <div style={{ flex: 1 }}>
              <span className="panel-kicker">РџР»Р°РЅРёСЂРѕРІР°РЅРёРµ</span>
              <h2 className="panel-title">Р“РµРЅРµСЂР°С†РёСЏ С‚РµРј</h2>
              <p className="form-hint" style={{ marginTop: "10px" }}>
                РњРѕР¶РЅРѕ РѕСЃС‚Р°РІРёС‚СЊ С‚РµРјСѓ РїСѓСЃС‚РѕР№, С‡С‚РѕР±С‹ СЃРёСЃС‚РµРјР° СЃР°РјР° СЃРѕР±СЂР°Р»Р° РёРґРµРё РїРѕ РєРѕРЅС‚РµРєСЃС‚Сѓ РїСЂРѕРґСѓРєС‚Р°. РР»Рё Р·Р°РґР°С‚СЊ СЃРїРµС†С‚РµРјСѓ Рё
                С‚РѕС‡РЅРѕРµ РєРѕР»РёС‡РµСЃС‚РІРѕ РїРѕСЃС‚РѕРІ РґР»СЏ РѕС‚РґРµР»СЊРЅРѕРіРѕ Р±Р»РѕРєР°.
              </p>
            </div>
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", justifyContent: "flex-end" }}>
              <PlanMixConfigurator planId={plan.id} initialMix={contentMix} />
              <QuickPostModal planId={plan.id} initialDirection={dominantDirection} channels={productChannels} />
              <form action={buildPlanMaterialsAction}>
                <input type="hidden" name="planId" value={plan.id} />
                <SubmitButton className="btn btn-primary" pendingLabel="РЎРѕР±РёСЂР°РµРј РјР°С‚РµСЂРёР°Р»С‹...">
                  РЎРѕР±СЂР°С‚СЊ РјР°С‚РµСЂРёР°Р»С‹
                </SubmitButton>
              </form>
              <Link href={`/products/${plan.product_id}`} className="btn">
                Рљ РїСЂРѕРґСѓРєС‚Сѓ
              </Link>
              <Link href="/" className="btn">
                РќР° РґР°С€Р±РѕСЂРґ
              </Link>
              <form action={deletePlanAction}>
                <input type="hidden" name="planId" value={plan.id} />
                <input type="hidden" name="productId" value={plan.product_id} />
                <SubmitButton className="btn" style={{ borderColor: "var(--danger)", color: "var(--danger)" }} pendingLabel="РЈРґР°Р»СЏРµРј РїР»Р°РЅ...">
                  РЈРґР°Р»РёС‚СЊ РїР»Р°РЅ
                </SubmitButton>
              </form>
            </div>
          </div>

          <form action={generatePlanItemsAction} style={{ display: "grid", gap: "16px", gridTemplateColumns: "1fr 180px auto" }}>
            <input type="hidden" name="planId" value={plan.id} />
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">РЎРїРµС†С‚РµРјР°</label>
              <input
                type="text"
                name="themeOverride"
                className="form-input"
                placeholder="РќР°РїСЂРёРјРµСЂ: РёРґРµРё РґР»СЏ Telegram Рѕ РїСЂРѕСЃС‚РѕРј РІРЅРµРґСЂРµРЅРёРё AI"
              />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">РЎРєРѕР»СЊРєРѕ РїРѕСЃС‚РѕРІ</label>
              <input type="number" name="numItems" className="form-input" min={1} max={30} placeholder="РђРІС‚Рѕ" />
            </div>
            <div style={{ display: "flex", alignItems: "end" }}>
              <SubmitButton className="btn btn-primary" pendingLabel="Р“РµРЅРµСЂРёСЂСѓРµРј С‚РµРјС‹...">
                РЎРіРµРЅРµСЂРёСЂРѕРІР°С‚СЊ С‚РµРјС‹
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
              РќРѕРІР°СЏ С‚РµРјР° РїРѕРґСЃРІРµС‡РµРЅР° РІ СЃРїРёСЃРєРµ РЅРёР¶Рµ.
            </div>
          ) : null}
        </article>

        {plan.settings_json?.needs_reschedule ? (
          <article className="panel" style={{ borderColor: "rgba(255, 196, 107, 0.45)", background: "rgba(255, 196, 107, 0.08)" }}>
            <div className="panel-header">
              <div>
                <span className="panel-kicker">Р Р°СЃРїРёСЃР°РЅРёРµ С‚СЂРµР±СѓРµС‚ РїРµСЂРµСЃРјРѕС‚СЂР°</span>
                <h2 className="panel-title">РћРґРёРЅ РёР· РїРѕСЃС‚РѕРІ СѓР¶Рµ РѕРїСѓР±Р»РёРєРѕРІР°РЅ РІСЂСѓС‡РЅСѓСЋ СЂР°РЅСЊС€Рµ СЃСЂРѕРєР°</h2>
              </div>
            </div>
            <p className="form-hint" style={{ marginTop: "10px" }}>
              РџРµСЂРµСЃРѕР±РµСЂРёС‚Рµ РјР°С‚РµСЂРёР°Р»С‹, С‡С‚РѕР±С‹ РєРѕРЅС‚РµРЅС‚-Р·Р°РІРѕРґ Р·Р°РЅРѕРІРѕ СЂР°Р·Р»РѕР¶РёР» РѕСЃС‚Р°РІС€РёРµСЃСЏ РїСѓР±Р»РёРєР°С†РёРё РїРѕ РєР°Р»РµРЅРґР°СЂСЋ.
            </p>
          </article>
        ) : null}

        <article className="panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">РљР°Р»РµРЅРґР°СЂСЊ</span>
              <h2 className="panel-title">РџР»Р°РЅ РїСѓР±Р»РёРєР°С†РёР№ РїРѕ РґРЅСЏРј</h2>
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
                            {dayItems.length ? `${dayItems.length} РїРѕСЃС‚` : ""}
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
                  <div className="panel-kicker">Р’С‹Р±СЂР°РЅРЅС‹Р№ РґРµРЅСЊ</div>
                  <h3 style={{ margin: "6px 0 0", fontSize: "1.05rem" }}>{formatDayLabel(selectedDay)}</h3>
                </div>
                <span className="badge badge-outline">{selectedDayItems.length} РІ РїР»Р°РЅРµ</span>
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
                            {item.title}
                          </Link>
                        </div>
                        <span className={getBadgeClass(item.status)}>{statusLabel(item.status)}</span>
                      </div>
                    ))}
                </div>
              ) : (
                <div className="empty-state compact-empty-state">
                  <strong>РќР° СЌС‚РѕС‚ РґРµРЅСЊ РїРѕСЃС‚РѕРІ РЅРµС‚</strong>
                </div>
              )}
            </div>
          </div>
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">РњР°С‚РµСЂРёР°Р»С‹</span>
              <h2 className="panel-title">РћС‡РµСЂРµРґСЊ РєРѕРЅС‚РµРЅС‚Р°</h2>
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
                        #{item.order + 1} В· {formatArticleType(item.article_type)}
                      </span>
                      <Link
                        href={`/content-plans/${plan.id}/items/${item.id}`}
                        className="list-item-title item-link"
                        style={{ fontSize: "1.1rem", textDecoration: "none" }}
                      >
                        {item.title}
                      </Link>
                      <p style={{ color: "var(--muted)", margin: "8px 0", fontSize: "0.9rem", maxWidth: "800px" }}>
                        {item.angle || "РЈРіРѕР» РїРѕРґР°С‡Рё РїРѕРєР° РЅРµ Р·Р°РґР°РЅ."}
                      </p>
                      <div style={{ display: "flex", gap: "8px", marginTop: "12px", flexWrap: "wrap" }}>
                        {isHighlighted ? <span className="badge badge-warning">РќРѕРІРѕРµ</span> : null}
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
                          <span aria-hidden="true">вњ“</span>
                          <span>РџРѕСЃС‚ РіРѕС‚РѕРІ</span>
                        </span>
                      ) : (
                        <span className={getBadgeClass(item.status)}>{statusLabel(item.status)}</span>
                      )}
                      <p style={{ margin: 0, color: "var(--muted)", fontSize: "0.85rem", textAlign: "right" }}>{getStatusHintClean(item.status)}</p>
                      {item.scheduled_at ? (
                        <p style={{ margin: 0, color: "var(--muted)", fontSize: "0.8rem", textAlign: "right" }}>
                          РџР»Р°РЅ: {new Date(item.scheduled_at).toLocaleString("ru-RU")}
                        </p>
                      ) : null}
                      {item.published_at ? (
                        <p style={{ margin: 0, color: "var(--muted)", fontSize: "0.8rem", textAlign: "right" }}>
                          РћРїСѓР±Р»РёРєРѕРІР°РЅРѕ: {new Date(item.published_at).toLocaleString("ru-RU")}
                        </p>
                      ) : null}
                      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", justifyContent: "flex-end" }}>
                        {shouldShowGenerateButton(item.status) ? (
                          <form action={generateItemBundleAction}>
                            <input type="hidden" name="planId" value={plan?.id ?? ""} />
                            <input type="hidden" name="itemId" value={item.id} />
                            <SubmitButton
                              className="btn btn-primary"
                              pendingLabel={item.status === "draft" ? "РџРµСЂРµРіРµРЅРµСЂРёСЂСѓРµРј РїРѕСЃС‚ Рё РёР»Р»СЋСЃС‚СЂР°С†РёСЋ..." : "Р“РµРЅРµСЂРёСЂСѓРµРј РїРѕСЃС‚ Рё РёР»Р»СЋСЃС‚СЂР°С†РёСЋ..."}
                            >
                              Р“РµРЅРµСЂР°С†РёСЏ
                            </SubmitButton>
                          </form>
                        ) : null}
                        {false ? (
                          <form action={moveStatusAction}>
                            <input type="hidden" name="planId" value={plan?.id ?? ""} />
                            <input type="hidden" name="itemId" value={item.id} />
                            <input type="hidden" name="status" value="review-ready" />
                            <SubmitButton className="btn" pendingLabel="РћС‚РјРµС‡Р°РµРј РїРѕСЃС‚ РєР°Рє РіРѕС‚РѕРІС‹Р№...">
                              Р“РѕС‚РѕРІРѕ
                            </SubmitButton>
                          </form>
                        ) : null}
                        {item.status === "draft" || item.status === "review-ready" || item.status === "published" ? (
                          <Link href={`/content-plans/${plan.id}/items/${item.id}`} className="btn">
                            РћС‚РєСЂС‹С‚СЊ РїРѕСЃС‚
                          </Link>
                        ) : null}
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="empty-state">
                <strong>Р’ РѕС‡РµСЂРµРґРё РїРѕРєР° РїСѓСЃС‚Рѕ</strong>
                <p>РќР°Р¶РјРёС‚Рµ В«РЎРіРµРЅРµСЂРёСЂРѕРІР°С‚СЊ С‚РµРјС‹В», С‡С‚РѕР±С‹ СЃРѕР±СЂР°С‚СЊ РЅРѕРІС‹Р№ РїР»Р°РЅ Рё РїРѕС‚РѕРј РїРµСЂРµР№С‚Рё Рє РіРµРЅРµСЂР°С†РёРё РјР°С‚РµСЂРёР°Р»РѕРІ.</p>
              </div>
            )}
          </div>
        </article>
      </section>
    </>
  );
}
