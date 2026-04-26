"use client";

import { useMemo, useState } from "react";

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
  const month = useMemo(() => getCurrentMonthValue(), []);
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
        theme: null,
        status: "draft",
        items: [],
      });

      window.location.href = `/content-plans/${plan.id}`;
    } catch {
      setMessage("Не удалось создать черновик контент-плана.");
      setIsCreating(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", justifyContent: "flex-end", alignItems: "center", gap: "12px" }}>
      {message ? <span style={{ color: "var(--danger)" }}>{message}</span> : null}
      <button type="submit" className="btn btn-primary" disabled={isCreating}>
        {isCreating ? "Создаем..." : "Создать план"}
      </button>
    </form>
  );
}
