"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { patchJson, postJson } from "@/lib/api";

type PlanGenerationControlsProps = {
  planId: string;
  initialMonth: string;
  initialTheme: string | null;
  initialAutoGenerateIllustrations: boolean;
  isJobActive: boolean;
  availableChannels: string[];
};

type JobResponse = {
  id: string;
  status: string;
};

const CHANNEL_LABELS: Record<string, string> = {
  telegram: "Telegram",
  dzen: "Дзен",
  vk: "VK",
  blog: "Блог",
  instagram: "Instagram",
  youtube: "YouTube",
};

function normalizeChannel(channel: string) {
  return channel.trim().toLowerCase();
}

function prettifyChannel(channel: string) {
  return CHANNEL_LABELS[channel] || channel;
}

export default function PlanGenerationControls({
  planId,
  initialMonth,
  initialTheme,
  initialAutoGenerateIllustrations,
  isJobActive,
  availableChannels,
}: PlanGenerationControlsProps) {
  const router = useRouter();
  const normalizedChannels = useMemo(
    () => [...new Set(availableChannels.map(normalizeChannel).filter(Boolean))],
    [availableChannels],
  );

  const [month, setMonth] = useState(initialMonth);
  const [theme, setTheme] = useState(initialTheme ?? "");
  const [generationTheme, setGenerationTheme] = useState("");
  const [numItems, setNumItems] = useState("");
  const [autoGenerateIllustrations, setAutoGenerateIllustrations] = useState(initialAutoGenerateIllustrations);
  const [selectedChannels, setSelectedChannels] = useState<string[]>(normalizedChannels);
  const [isSaving, setIsSaving] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [message, setMessage] = useState("");

  const allChannelsSelected = normalizedChannels.length > 0 && normalizedChannels.every((channel) => selectedChannels.includes(channel));

  async function savePlanSettings() {
    const cleanTheme = theme.trim();
    await patchJson(`/content-plans/${planId}`, {
      month,
      theme: cleanTheme || null,
      settings_json: {
        auto_generate_illustrations: autoGenerateIllustrations,
      },
    });
    return cleanTheme;
  }

  function toggleChannel(channel: string) {
    setSelectedChannels((current) => (current.includes(channel) ? current.filter((item) => item !== channel) : [...current, channel]));
  }

  function toggleAllChannels() {
    setSelectedChannels(allChannelsSelected ? [] : normalizedChannels);
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

  async function handleGenerateMaterials(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");

    const firstConfirm = window.confirm("Добавить новые материалы в текущий контент-план?");
    if (!firstConfirm) return;

    const secondConfirm = window.confirm("Точно запускаем? Новые материалы будут добавлены в этот же план.");
    if (!secondConfirm) return;

    setIsStarting(true);
    try {
      await savePlanSettings();
      const cleanGenerationTheme = generationTheme.trim();
      const cleanNumItems = numItems.trim();
      const parsedNumItems = cleanNumItems ? Number(cleanNumItems) : undefined;

      await postJson<JobResponse>(`/content-plans/${planId}/run-pipeline`, {
        generate_items: true,
        theme: cleanGenerationTheme || null,
        num_items: parsedNumItems !== undefined && Number.isFinite(parsedNumItems) && parsedNumItems > 0 ? parsedNumItems : null,
        channel_targets: selectedChannels,
      });

      setMessage("Генерация запущена. Новые материалы будут добавлены в этот план.");
      router.refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Не удалось запустить генерацию.");
    } finally {
      setIsStarting(false);
    }
  }

  async function handleStopGeneration() {
    const confirmed = window.confirm("Остановить текущую генерацию?");
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
    <form onSubmit={handleGenerateMaterials} style={{ display: "grid", gap: "16px" }}>
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
            placeholder="Например: Общеобразовательный"
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

      <div className="form-group" style={{ marginBottom: 0 }}>
        <label className="form-label">Тема добавляемых постов</label>
        <input
          type="text"
          className="form-input"
          placeholder="Например: 5 постов про AI для Дзена. Можно оставить пустым."
          value={generationTheme}
          onChange={(event) => setGenerationTheme(event.target.value)}
        />
      </div>

      {normalizedChannels.length > 0 ? (
        <div
          style={{
            display: "grid",
            gap: "10px",
            padding: "14px 16px",
            border: "1px solid var(--border)",
            borderRadius: "14px",
            background: "rgba(255,255,255,0.55)",
          }}
        >
          <strong>Каналы для новых материалов</strong>
          <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
            <label style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
              <input type="checkbox" checked={allChannelsSelected} onChange={toggleAllChannels} />
              <span>Все каналы</span>
            </label>

            {normalizedChannels.map((channel) => (
              <label key={channel} style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
                <input type="checkbox" checked={selectedChannels.includes(channel)} onChange={() => toggleChannel(channel)} />
                <span>{prettifyChannel(channel)}</span>
              </label>
            ))}
          </div>
        </div>
      ) : null}

      <label
        style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          padding: "14px 16px",
          border: "1px solid var(--border)",
          borderRadius: "14px",
          background: "rgba(255,255,255,0.55)",
          color: "var(--text)",
        }}
      >
        <input
          type="checkbox"
          checked={autoGenerateIllustrations}
          onChange={(event) => setAutoGenerateIllustrations(event.target.checked)}
        />
        <span>Генерировать иллюстрации сразу</span>
      </label>

      <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end", alignItems: "center", flexWrap: "wrap" }}>
        {message ? <span className="form-hint" style={{ marginRight: "auto" }}>{message}</span> : null}
        <button type="button" className="btn" onClick={handleSaveSettings} disabled={isSaving || isStarting || isJobActive}>
          {isSaving ? "Сохраняем..." : "Сохранить настройки"}
        </button>
        <button type="button" className="btn" onClick={handleStopGeneration} disabled={!isJobActive || isStopping}>
          {isStopping ? "Останавливаем..." : "Остановить генерацию"}
        </button>
        <button type="submit" className="btn btn-primary" disabled={isStarting || isJobActive || selectedChannels.length === 0}>
          {isStarting ? "Запускаем..." : "Сгенерировать материалы"}
        </button>
      </div>
    </form>
  );
}
