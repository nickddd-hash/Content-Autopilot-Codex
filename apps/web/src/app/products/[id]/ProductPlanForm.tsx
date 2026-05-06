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

function getCurrentMonthValue(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return `${now.getFullYear()}-${month}`;
}

const FREQUENCY_OPTIONS = [
  { label: "1 раз в неделю", postsPerWeek: 1, defaultCount: 4 },
  { label: "2 раза в неделю", postsPerWeek: 2, defaultCount: 8 },
  { label: "3 раза в неделю", postsPerWeek: 3, defaultCount: 12 },
  { label: "Каждый день", postsPerWeek: 7, defaultCount: 30 },
];

export default function ProductPlanForm({ productId }: ProductPlanFormProps) {
  const currentMonth = useMemo(() => getCurrentMonthValue(), []);
  const [theme, setTheme] = useState("");
  const [frequencyIndex, setFrequencyIndex] = useState(1);
  const [numItems, setNumItems] = useState(FREQUENCY_OPTIONS[1].defaultCount);
  const [generateIllustrations, setGenerateIllustrations] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [message, setMessage] = useState("");

  function handleFrequencyChange(index: number) {
    setFrequencyIndex(index);
    setNumItems(FREQUENCY_OPTIONS[index].defaultCount);
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsCreating(true);
    setMessage("");

    try {
      const plan = await postJson<ContentPlanResponse>("/content-plans", {
        product_id: productId,
        month: currentMonth,
        theme: theme.trim() || null,
        status: "draft",
        items: [],
        settings_json: {
          num_items_default: numItems,
          frequency_label: FREQUENCY_OPTIONS[frequencyIndex].label,
          auto_generate_illustrations: generateIllustrations,
        },
      });

      window.location.href = `/content-plans/${plan.id}`;
    } catch {
      setMessage("Не удалось создать контент-план.");
      setIsCreating(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
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
            Количество постов
            <HelpHint text="Сколько постов сгенерировать. Рассчитано автоматически по частоте, можно изменить вручную." />
          </label>
          <input
            type="number"
            className="form-input"
            min={1}
            max={30}
            value={numItems}
            onChange={(e) => setNumItems(Math.min(30, Math.max(1, Number(e.target.value))))}
            required
          />
        </div>
      </div>

      <div className="form-group" style={{ marginBottom: 0 }}>
        <label className="form-label form-label-inline">
          Тема плана
          <HelpHint text="Можно оставить пустой: тогда темы подберутся по контексту продукта." />
        </label>
        <input
          type="text"
          className="form-input"
          placeholder="Необязательно"
          value={theme}
          onChange={(e) => setTheme(e.target.value)}
        />
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "14px 16px",
          borderRadius: "12px",
          border: "1px solid var(--border)",
          background: "rgba(255,255,255,0.03)",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <strong style={{ fontSize: "14px" }}>Автогенерация иллюстраций</strong>
            <HelpHint text="Если включено, для каждого поста при генерации будет автоматически создаваться иллюстрация. Можно включить позже вручную для каждого поста." />
          </div>
          <p style={{ fontSize: "12px", color: "var(--text-muted)", margin: "2px 0 0" }}>
            По умолчанию выключено — иллюстрации генерируются вручную
          </p>
        </div>
        <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={generateIllustrations}
            onChange={(e) => setGenerateIllustrations(e.target.checked)}
          />
          <span style={{ fontSize: "13px", color: "var(--text-muted)" }}>
            {generateIllustrations ? "Включено" : "Выключено"}
          </span>
        </label>
      </div>

      <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "center", gap: "12px" }}>
        {message ? <span style={{ color: "var(--danger)" }}>{message}</span> : null}
        <button type="submit" className="btn btn-primary" disabled={isCreating}>
          {isCreating ? "Создаём..." : "Создать план"}
        </button>
      </div>
    </form>
  );
}
