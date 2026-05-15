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

const FREQUENCY_OPTIONS = [
  { label: "1 раз в неделю", postsPerWeek: 1 },
  { label: "2 раза в неделю", postsPerWeek: 2 },
  { label: "3 раза в неделю", postsPerWeek: 3 },
  { label: "Каждый день", postsPerWeek: 7 },
];

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

function formatMonthLabel(startStr: string, endStr: string): string {
  const start = new Date(startStr + "T00:00:00");
  const end = new Date(endStr + "T00:00:00");
  const fmt = (d: Date) =>
    d.toLocaleDateString("ru-RU", { month: "long", year: "numeric" });
  if (
    start.getMonth() === end.getMonth() &&
    start.getFullYear() === end.getFullYear()
  ) {
    return fmt(start);
  }
  return `${fmt(start)} – ${fmt(end)}`;
}

export default function ProductPlanForm({ productId }: ProductPlanFormProps) {
  const today = useMemo(() => new Date(), []);
  const defaultStart = useMemo(() => toDateInputValue(today), [today]);
  const defaultEnd = useMemo(() => toDateInputValue(addDays(today, 28)), [today]);

  const [startDate, setStartDate] = useState(defaultStart);
  const [endDate, setEndDate] = useState(defaultEnd);
  const [frequencyIndex, setFrequencyIndex] = useState(1);
  const [theme, setTheme] = useState("");
  const [genTopics, setGenTopics] = useState(true);
  const [genPosts, setGenPosts] = useState(true);
  const [genIllustrations, setGenIllustrations] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState("");

  const selectedFrequency = FREQUENCY_OPTIONS[frequencyIndex];
  const postCount = calcPostCount(startDate, endDate, selectedFrequency.postsPerWeek);
  const dateRangeValid = startDate && endDate && endDate >= startDate;

  function handleFrequencyChange(index: number) {
    setFrequencyIndex(index);
  }

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

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!dateRangeValid) return;

    setIsCreating(true);
    setError("");

    try {
      const plan = await postJson<ContentPlanResponse>("/content-plans", {
        product_id: productId,
        month: formatMonthLabel(startDate, endDate),
        theme: theme.trim() || null,
        status: "draft",
        items: [],
        settings_json: {
          num_items_default: postCount,
          frequency_label: selectedFrequency.label,
          auto_generate_illustrations: genIllustrations,
          date_range_start: startDate,
          date_range_end: endDate,
        },
      });

      if (genTopics) {
        await postJson(`/content-plans/${plan.id}/run-pipeline`, {
          generate_items: true,
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

      {/* Date range */}
      <div>
        <div className="form-label form-label-inline" style={{ marginBottom: "10px" }}>
          Период плана
          <HelpHint text="Выберите диапазон дат — количество постов рассчитается автоматически по частоте." />
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
            onChange={(e) => handleFrequencyChange(Number(e.target.value))}
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
              color: "var(--text)",
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

      {/* Theme */}
      <div className="form-group" style={{ marginBottom: 0 }}>
        <label className="form-label form-label-inline">
          Тема плана
          <HelpHint text="Необязательно. Если задать — темы постов будут подобраны внутри этой темы." />
        </label>
        <input
          type="text"
          className="form-input"
          placeholder="Необязательно"
          value={theme}
          onChange={(e) => setTheme(e.target.value)}
        />
      </div>

      {/* Generation checkboxes */}
      <div
        style={{
          borderRadius: "14px",
          border: "1px solid var(--border)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            padding: "12px 16px",
            background: "rgba(255,255,255,0.03)",
            borderBottom: "1px solid var(--border)",
            fontSize: "13px",
            fontWeight: 600,
            color: "var(--muted)",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          Сгенерировать сразу
          <HelpHint text="Выберите, что запустить автоматически после создания плана. Всё можно запустить вручную позже." />
        </div>

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

      <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "center", gap: "12px" }}>
        {error ? <span style={{ color: "var(--danger)", fontSize: "13px" }}>{error}</span> : null}
        <button type="submit" className="btn btn-primary" disabled={isCreating || !dateRangeValid}>
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
        transition: "background 0.15s",
        background: checked && !disabled ? "rgba(176, 191, 119, 0.06)" : "transparent",
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
