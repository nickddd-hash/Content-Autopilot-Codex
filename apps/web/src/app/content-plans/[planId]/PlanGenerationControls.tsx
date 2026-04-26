"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { patchJson, postJson } from "@/lib/api";

type PlanGenerationControlsProps = {
  planId: string;
  initialMonth: string;
  initialTheme: string | null;
  isJobActive: boolean;
};

type JobResponse = {
  id: string;
  status: string;
};

export default function PlanGenerationControls({
  planId,
  initialMonth,
  initialTheme,
  isJobActive,
}: PlanGenerationControlsProps) {
  const router = useRouter();
  const [month, setMonth] = useState(initialMonth);
  const [theme, setTheme] = useState(initialTheme ?? "");
  const [numItems, setNumItems] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [message, setMessage] = useState("");

  async function savePlanSettings() {
    const cleanTheme = theme.trim();
    await patchJson(`/content-plans/${planId}`, {
      month,
      theme: cleanTheme || null,
    });
    return cleanTheme;
  }

  async function handleSaveSettings() {
    setIsSaving(true);
    setMessage("");
    try {
      await savePlanSettings();
      setMessage("Настройки сохранены.");
      router.refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Не удалось сохранить настройки.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleCreatePlan(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");

    const firstConfirm = window.confirm("Запустить генерацию контент-плана? Это может занять несколько минут.");
    if (!firstConfirm) return;

    const secondConfirm = window.confirm("Точно запускаем? Будут созданы темы, посты, иллюстрации и расписание.");
    if (!secondConfirm) return;

    setIsStarting(true);
    try {
      const cleanTheme = await savePlanSettings();
      const cleanNumItems = numItems.trim();
      const parsedNumItems = cleanNumItems ? Number(cleanNumItems) : undefined;

      await postJson<JobResponse>(`/content-plans/${planId}/run-pipeline`, {
        generate_items: true,
        theme: cleanTheme || null,
        num_items: parsedNumItems !== undefined && Number.isFinite(parsedNumItems) && parsedNumItems > 0 ? parsedNumItems : null,
      });

      setMessage("Генерация запущена. Страница будет обновляться автоматически.");
      router.refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Не удалось запустить генерацию.");
    } finally {
      setIsStarting(false);
    }
  }

  async function handleStopGeneration() {
    const confirmed = window.confirm("Остановить текущую генерацию контент-плана?");
    if (!confirmed) return;

    setIsStopping(true);
    setMessage("");
    try {
      await postJson<JobResponse>(`/content-plans/${planId}/cancel-pipeline`, {});
      setMessage("Генерация остановлена.");
      router.refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Не удалось остановить генерацию.");
    } finally {
      setIsStopping(false);
    }
  }

  return (
    <form onSubmit={handleCreatePlan} style={{ display: "grid", gap: "16px" }}>
      <div style={{ display: "grid", gap: "16px", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="form-label">Месяц</label>
          <input type="month" className="form-input" value={month} onChange={(event) => setMonth(event.target.value)} required />
        </div>
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="form-label">Название плана</label>
          <input
            type="text"
            className="form-input"
            placeholder="Например: AI без сложности - апрель"
            value={theme}
            onChange={(event) => setTheme(event.target.value)}
          />
        </div>
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="form-label">Сколько постов</label>
          <input
            type="number"
            className="form-input"
            min={1}
            max={30}
            placeholder="Авто"
            value={numItems}
            onChange={(event) => setNumItems(event.target.value)}
          />
        </div>
      </div>

      <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end", alignItems: "center", flexWrap: "wrap" }}>
        {message ? <span className="form-hint" style={{ marginRight: "auto" }}>{message}</span> : null}
        <button type="button" className="btn" onClick={handleSaveSettings} disabled={isSaving || isStarting || isJobActive}>
          {isSaving ? "Сохраняем..." : "Сохранить настройки"}
        </button>
        <button type="button" className="btn" onClick={handleStopGeneration} disabled={!isJobActive || isStopping}>
          {isStopping ? "Останавливаем..." : "Остановить генерацию"}
        </button>
        <button type="submit" className="btn btn-primary" disabled={isStarting || isJobActive}>
          {isStarting ? "Запускаем..." : "Создать план"}
        </button>
      </div>
    </form>
  );
}
