"use client";

import { useMemo, useState } from "react";

import HelpHint from "@/components/HelpHint";
import { postJson } from "@/lib/api";

type ProductPlanFormProps = {
  productId: string;
};

type ContentPlanResponse = {
  id: string;
};

type MixKey = "practical" | "educational" | "news" | "opinion" | "critical";

const FREQUENCY_OPTIONS = [
  { label: "1 раз в неделю", postsPerWeek: 1 },
  { label: "2 раза в неделю", postsPerWeek: 2 },
  { label: "3 раза в неделю", postsPerWeek: 3 },
  { label: "Каждый день", postsPerWeek: 7 },
];

const DIRECTION_META: Array<{ key: MixKey; label: string; description: string }> = [
  { key: "practical", label: "Practical", description: "Бизнес-ситуации, кейсы, прикладная польза и конкретные сценарии." },
  { key: "educational", label: "Educational", description: "Простые объяснения AI и полезные трюки без перегруза." },
  { key: "news", label: "News", description: "Важные AI-новости с понятным практическим выводом." },
  { key: "opinion", label: "Opinion", description: "Личный взгляд, backstage и авторская интерпретация." },
  { key: "critical", label: "Critical", description: "Ограничения, риски, трезвый взгляд на AI." },
];

const DEFAULT_MIX: Record<MixKey, number> = {
  practical: 60,
  educational: 20,
  news: 10,
  opinion: 5,
  critical: 5,
};

function toDateInputValue(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function addDays(date: Date, days: number): Date {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}

function calcPostCount(startStr: string, endStr: string, postsPerWeek: number): number {
  const start = new Date(startStr);
  const end = new Date(endStr);
  const days = Math.max(0, Math.ceil((end.getTime() - start.getTime()) / 86400000));
  return Math.max(1, Math.round((days / 7) * postsPerWeek));
}


export default function ProductPlanForm({ productId }: ProductPlanFormProps) {
  const today = useMemo(() => new Date(), []);
  const defaultStart = useMemo(() => toDateInputValue(today), [today]);
  const defaultEnd = useMemo(() => toDateInputValue(addDays(today, 28)), [today]);

  const [startDate, setStartDate] = useState(defaultStart);
  const [endDate, setEndDate] = useState(defaultEnd);
  const [frequencyIndex, setFrequencyIndex] = useState(1);
  const [name, setName] = useState("");
  const [mix, setMix] = useState<Record<MixKey, number>>({ ...DEFAULT_MIX });
  const [genTopics, setGenTopics] = useState(true);
  const [genPosts, setGenPosts] = useState(true);
  const [genIllustrations, setGenIllustrations] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState("");

  const selectedFrequency = FREQUENCY_OPTIONS[frequencyIndex];
  const postCount = calcPostCount(startDate, endDate, selectedFrequency.postsPerWeek);
  const dateRangeValid = startDate && endDate && endDate >= startDate;
  const mixTotal = Object.values(mix).reduce((sum, v) => sum + v, 0);
  const mixValid = mixTotal === 100;

  function handleGenTopicsChange(checked: boolean) {
    setGenTopics(checked);
    if (!checked) {
      setGenPosts(false);
      setGenIllustrations(false);
    }
  }

  function handleGenPostsChange(checked: boolean) {
    setGenPosts(checked);
    if (!checked) setGenIllustrations(false);
  }

  function toggleMixDirection(key: MixKey, checked: boolean) {
    setMix((current) => {
      const next = { ...current };
      if (!checked) {
        next[key] = 0;
        return next;
      }
      const remaining = Math.max(0, 100 - Object.values(current).reduce((s, v) => s + v, 0));
      next[key] = current[key] > 0 ? current[key] : Math.min(20, remaining);
      return next;
    });
  }

  function updateMixValue(key: MixKey, requested: number) {
    setMix((current) => {
      const otherTotal = Object.entries(current)
        .filter(([k]) => k !== key)
        .reduce((s, [, v]) => s + v, 0);
      const maxAllowed = Math.max(0, 100 - otherTotal);
      return { ...current, [key]: Math.max(0, Math.min(requested, maxAllowed)) };
    });
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!dateRangeValid || !mixValid) return;

    setIsCreating(true);
    setError("");

    try {
      const plan = await postJson<ContentPlanResponse>("/content-plans", {
        product_id: productId,
        month: startDate.slice(0, 7),
        theme: name.trim() || null,
        status: "draft",
        items: [],
        settings_json: {
          num_items_default: postCount,
          frequency_label: selectedFrequency.label,
          auto_generate_illustrations: genIllustrations,
          date_range_start: startDate,
          date_range_end: endDate,
          content_mix: mix,
        },
      });

      if (genTopics) {
        await postJson(`/content-plans/${plan.id}/run-pipeline`, {
          generate_items: true,
          build_materials: genPosts,
          num_items: postCount,
        });
      }

      window.location.href = `/content-plans/${plan.id}`;
    } catch {
      setError("Не удалось создать контент-план. Попробуйте ещё раз.");
      setIsCreating(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "24px" }}>

      {/* Plan name */}
      <div className="form-group" style={{ marginBottom: 0 }}>
        <label className="form-label form-label-inline">
          Название плана
          <HelpHint text="Отображается в списке планов. Например: «Май — AI для бизнеса» или «Q2 запуск»." />
        </label>
        <input
          type="text"
          className="form-input"
          placeholder="Например: Май — AI без сложности"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </div>

      {/* Date range */}
      <div>
        <div className="form-label form-label-inline" style={{ marginBottom: "10px", display: "flex", alignItems: "center", gap: "6px" }}>
          Период плана
          <HelpHint text="Количество постов рассчитается автоматически по диапазону и частоте." />
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", gap: "10px", alignItems: "center" }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label" style={{ fontSize: "12px" }}>Начало</label>
            <input
              type="date"
              className="form-input"
              value={startDate}
              min={toDateInputValue(today)}
              onChange={(e) => {
                setStartDate(e.target.value);
                if (e.target.value > endDate) setEndDate(e.target.value);
              }}
              required
            />
          </div>
          <span style={{ color: "var(--muted)", paddingTop: "20px" }}>—</span>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label" style={{ fontSize: "12px" }}>Конец</label>
            <input
              type="date"
              className="form-input"
              value={endDate}
              min={startDate || toDateInputValue(today)}
              onChange={(e) => setEndDate(e.target.value)}
              required
            />
          </div>
        </div>
      </div>

      {/* Frequency + calculated count */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="form-label form-label-inline">
            Частота публикаций
            <HelpHint text="Как часто планируете публиковать посты." />
          </label>
          <select
            className="form-input"
            value={frequencyIndex}
            onChange={(e) => setFrequencyIndex(Number(e.target.value))}
          >
            {FREQUENCY_OPTIONS.map((opt, i) => (
              <option key={i} value={i}>{opt.label}</option>
            ))}
          </select>
        </div>

        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="form-label form-label-inline">
            Постов в плане
            <HelpHint text="Рассчитывается автоматически: период × частота." />
          </label>
          <div
            className="form-input"
            style={{
              display: "flex",
              alignItems: "center",
              background: "rgba(255,255,255,0.04)",
              cursor: "default",
              userSelect: "none",
            }}
          >
            <strong>{postCount}</strong>
            <span style={{ marginLeft: "8px", fontSize: "12px", color: "var(--muted)" }}>
              {selectedFrequency.label.toLowerCase()}
            </span>
          </div>
        </div>
      </div>

      {/* Content mix */}
      <div>
        <div className="form-label form-label-inline" style={{ marginBottom: "10px", display: "flex", alignItems: "center", gap: "6px" }}>
          Микс контента
          <HelpHint text="Задайте долю каждого направления. Сумма должна быть ровно 100%." />
        </div>
        <div
          style={{
            border: "1px solid var(--border)",
            borderRadius: "14px",
            overflow: "hidden",
          }}
        >
          {DIRECTION_META.map((dir, idx) => {
            const enabled = mix[dir.key] > 0;
            const otherTotal = Object.entries(mix)
              .filter(([k]) => k !== dir.key)
              .reduce((s, [, v]) => s + v, 0);
            const maxAllowed = Math.max(mix[dir.key], 100 - otherTotal);
            const isLast = idx === DIRECTION_META.length - 1;

            return (
              <div
                key={dir.key}
                style={{
                  display: "grid",
                  gridTemplateColumns: "minmax(0,1fr) minmax(180px,240px)",
                  gap: "16px",
                  alignItems: "center",
                  padding: "12px 16px",
                  borderBottom: isLast ? "none" : "1px solid var(--border)",
                  background: enabled ? "rgba(176,191,119,0.05)" : "transparent",
                  opacity: enabled ? 1 : 0.55,
                  transition: "background 0.15s, opacity 0.15s",
                }}
              >
                <label style={{ display: "flex", gap: "10px", alignItems: "flex-start", cursor: "pointer" }}>
                  <input
                    type="checkbox"
                    checked={enabled}
                    onChange={(e) => toggleMixDirection(dir.key, e.target.checked)}
                    style={{ marginTop: "3px", flexShrink: 0 }}
                  />
                  <div>
                    <div style={{ fontSize: "14px", fontWeight: 600 }}>{dir.label}</div>
                    <div style={{ fontSize: "12px", color: "var(--muted)", marginTop: "2px", lineHeight: 1.4 }}>
                      {dir.description}
                    </div>
                  </div>
                </label>

                <div style={{ display: "grid", gap: "6px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
                    <span style={{ color: "var(--muted)" }}>Доля</span>
                    <strong>{mix[dir.key]}%</strong>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={maxAllowed}
                    step={5}
                    value={mix[dir.key]}
                    disabled={!enabled}
                    onChange={(e) => updateMixValue(dir.key, Number(e.target.value))}
                  />
                </div>
              </div>
            );
          })}

          <div
            style={{
              padding: "10px 16px",
              borderTop: "1px solid var(--border)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              fontSize: "13px",
              background: mixValid
                ? "rgba(176,191,119,0.08)"
                : "rgba(255,166,0,0.08)",
              color: mixValid ? "var(--text)" : "rgba(255,166,0,0.9)",
            }}
          >
            <span>Сумма: <strong>{mixTotal}%</strong></span>
            {mixValid
              ? <span style={{ color: "rgba(176,191,119,0.9)" }}>✓ Готово</span>
              : <span>Нужно ровно 100%</span>}
          </div>
        </div>
      </div>

      {/* Generation checkboxes */}
      <div>
        <div className="form-label form-label-inline" style={{ marginBottom: "10px", display: "flex", alignItems: "center", gap: "6px" }}>
          Сгенерировать сразу
          <HelpHint text="Что запустить автоматически после создания. Всё можно запустить вручную позже." />
        </div>
        <div style={{ border: "1px solid var(--border)", borderRadius: "14px", overflow: "hidden" }}>
          <CheckboxRow
            label="Темы"
            description="Заголовки и углы подачи для каждого поста"
            checked={genTopics}
            onChange={handleGenTopicsChange}
          />
          <CheckboxRow
            label="Посты"
            description="Черновики текстов на основе тем"
            checked={genPosts}
            disabled={!genTopics}
            onChange={handleGenPostsChange}
            indent
          />
          <CheckboxRow
            label="Иллюстрации"
            description="Изображения для каждого поста"
            checked={genIllustrations}
            disabled={!genPosts}
            onChange={setGenIllustrations}
            indent
            last
          />
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "center", gap: "12px" }}>
        {error ? <span style={{ color: "var(--danger)", fontSize: "13px" }}>{error}</span> : null}
        {!mixValid && (
          <span style={{ color: "rgba(255,166,0,0.9)", fontSize: "13px" }}>
            Микс контента должен быть 100%
          </span>
        )}
        <button
          type="submit"
          className="btn btn-primary"
          disabled={isCreating || !dateRangeValid || !mixValid}
        >
          {isCreating
            ? genTopics ? "Создаём и запускаем..." : "Создаём план..."
            : "Создать план"}
        </button>
      </div>
    </form>
  );
}

type CheckboxRowProps = {
  label: string;
  description: string;
  checked: boolean;
  disabled?: boolean;
  indent?: boolean;
  last?: boolean;
  onChange: (checked: boolean) => void;
};

function CheckboxRow({ label, description, checked, disabled = false, indent = false, last = false, onChange }: CheckboxRowProps) {
  return (
    <label
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "14px 16px",
        paddingLeft: indent ? "32px" : "16px",
        borderBottom: last ? "none" : "1px solid var(--border)",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.45 : 1,
        background: checked && !disabled ? "rgba(176,191,119,0.06)" : "transparent",
        transition: "background 0.15s",
      }}
    >
      <div>
        <div style={{ fontSize: "14px", fontWeight: 500 }}>{label}</div>
        <div style={{ fontSize: "12px", color: "var(--muted)", marginTop: "2px" }}>{description}</div>
      </div>
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(e) => onChange(e.target.checked)}
        style={{ width: "16px", height: "16px", cursor: disabled ? "not-allowed" : "pointer" }}
      />
    </label>
  );
}
