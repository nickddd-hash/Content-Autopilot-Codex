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

export default function ProductPlanForm({ productId }: ProductPlanFormProps) {
  const initialMonth = useMemo(() => getCurrentMonthValue(), []);
  const [month, setMonth] = useState(initialMonth);
  const [theme, setTheme] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [message, setMessage] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsCreating(true);
    setMessage("");

    try {
      const plan = await postJson<ContentPlanResponse>("/content-plans", {
        product_id: productId,
        month,
        theme: theme.trim() || null,
        status: "draft",
        items: [],
      });

      await postJson(`/content-plans/${plan.id}/run-pipeline`, {
        generate_items: true,
        theme: theme.trim() || null,
      });
      window.location.href = `/content-plans/${plan.id}`;
    } catch {
      setMessage("Не удалось создать и запустить сборку контент-плана.");
      setIsCreating(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "220px minmax(0, 1fr)",
          gap: "16px",
          alignItems: "end",
        }}
      >
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="form-label">Месяц</label>
          <input type="month" className="form-input" value={month} onChange={(event) => setMonth(event.target.value)} required />
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
            onChange={(event) => setTheme(event.target.value)}
          />
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "center", gap: "12px" }}>
        {message ? <span style={{ color: "var(--danger)" }}>{message}</span> : null}
        <button type="submit" className="btn btn-primary" disabled={isCreating}>
          {isCreating ? "Создаём..." : "Создать контент-план"}
        </button>
      </div>
    </form>
  );
}
