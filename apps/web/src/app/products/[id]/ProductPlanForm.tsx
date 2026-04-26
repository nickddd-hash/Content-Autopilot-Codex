"use client";

import { useState } from "react";

import { postJson } from "@/lib/api";

type ProductPlanFormProps = {
  productId: string;
  hasMainPlan: boolean;
};

type ContentPlanResponse = {
  id: string;
};

export default function ProductPlanForm({ productId, hasMainPlan }: ProductPlanFormProps) {
  const [isOpening, setIsOpening] = useState(false);
  const [message, setMessage] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsOpening(true);
    setMessage("");

    try {
      const plan = await postJson<ContentPlanResponse>("/content-plans/main", {
        product_id: productId,
      });

      window.location.href = `/content-plans/${plan.id}`;
    } catch {
      setMessage("Не удалось открыть основной контент-план.");
      setIsOpening(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", justifyContent: "flex-end", alignItems: "center", gap: "12px" }}>
      {message ? <span style={{ color: "var(--danger)" }}>{message}</span> : null}
      <button type="submit" className="btn btn-primary" disabled={isOpening}>
        {isOpening ? "Открываем..." : hasMainPlan ? "Открыть основной план" : "Создать основной план"}
      </button>
    </form>
  );
}
