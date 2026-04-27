"use client";

import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";

import HelpHint from "@/components/HelpHint";
import { postJson } from "@/lib/api";

type ContentDirection = "practical" | "educational" | "news" | "opinion" | "critical";

type QuickPostModalProps = {
  planId: string;
  initialDirection?: ContentDirection;
  channels: string[];
};

type QuickPostResponse = {
  id: string;
};

const DIRECTION_OPTIONS: Array<{ value: ContentDirection; label: string; description: string }> = [
  { value: "practical", label: "Практика", description: "Кейсы, польза, применение и конкретные сценарии." },
  { value: "educational", label: "Объясняющий", description: "Простое и спокойное объяснение темы без перегруза." },
  { value: "news", label: "Новости", description: "Реакция на важные обновления и события в AI." },
  { value: "opinion", label: "Мнение", description: "Личный взгляд, свободная или философская рамка." },
  { value: "critical", label: "Критический", description: "Ограничения, переоценка и трезвый взгляд без хайпа." },
];

function formatChannelLabel(channel: string) {
  const normalized = channel.toLowerCase();
  if (normalized === "telegram") return "Telegram";
  if (normalized === "dzen") return "Дзен";
  if (normalized === "blog") return "Блог";
  if (normalized === "vk") return "VK";
  return channel;
}

export default function QuickPostModal({
  planId,
  initialDirection = "educational",
  channels,
}: QuickPostModalProps) {
  const normalizedChannels = useMemo(
    () => channels.map((channel) => channel.trim()).filter(Boolean),
    [channels],
  );
  const [mounted, setMounted] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [contentDirection, setContentDirection] = useState<ContentDirection>(initialDirection);
  const [selectedChannels, setSelectedChannels] = useState<string[]>(normalizedChannels);
  const [includeIllustration, setIncludeIllustration] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState<"save" | "generate" | null>(null);
  const [error, setError] = useState("");

  const canSave = title.trim().length > 0 && text.trim().length > 0 && selectedChannels.length > 0 && !isSubmitting;
  const canGenerate = text.trim().length > 0 && selectedChannels.length > 0 && !isSubmitting;
  const selectedDirection = useMemo(
    () => DIRECTION_OPTIONS.find((option) => option.value === contentDirection) ?? DIRECTION_OPTIONS[1],
    [contentDirection],
  );

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    setSelectedChannels(normalizedChannels);
    setIncludeIllustration(true);
  }, [normalizedChannels, isOpen]);

  function toggleChannel(channel: string) {
    setSelectedChannels((current) => {
      if (current.includes(channel)) {
        return current.filter((item) => item !== channel);
      }
      return [...current, channel];
    });
  }

  async function handleSubmit(generateNow: boolean) {
    setError("");
    setIsSubmitting(generateNow ? "generate" : "save");

    try {
      const item = await postJson<QuickPostResponse>(`/content-plans/${planId}/quick-post`, {
        title: title.trim() || null,
        text: text.trim(),
        content_direction: contentDirection,
        channel_targets: selectedChannels,
        include_illustration: includeIllustration,
        generate_now: generateNow,
      });

      window.location.href = `/content-plans/${planId}/items/${item.id}`;
    } catch {
      setError("Не удалось добавить пост в план.");
      setIsSubmitting(null);
    }
  }

  const modal = isOpen ? (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(4, 6, 12, 0.82)",
        backdropFilter: "blur(8px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
        zIndex: 10000,
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: "min(760px, 100%)",
          height: "min(90vh, 900px)",
          overflow: "hidden",
          background: "#101114",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "20px",
          boxShadow: "0 30px 80px rgba(0,0,0,0.45)",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          style={{
            padding: "24px 24px 0",
            display: "flex",
            justifyContent: "space-between",
            gap: "12px",
            alignItems: "flex-start",
          }}
        >
          <div>
            <div className="panel-kicker">Быстрое добавление</div>
            <h2 style={{ margin: "8px 0 0", fontSize: "1.4rem", color: "#f5f7f1", display: "inline-flex", alignItems: "center", gap: "8px" }}>
              Новый пост в план
              <HelpHint text="Можно вставить готовый текст или дать тезисы и попросить ИИ собрать пост." />
            </h2>
          </div>
          <button type="button" className="btn" onClick={() => setIsOpen(false)}>
            Закрыть
          </button>
        </div>

        <div
          style={{
            padding: "20px 24px 0",
            flex: 1,
            minHeight: 0,
            overflowY: "auto",
            display: "grid",
            gap: "18px",
          }}
        >
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label" style={{ color: "#f5f7f1" }}>
              Заголовок поста
            </label>
            <input
              className="form-input"
              placeholder="Можно оставить пустым"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
            />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label form-label-inline" style={{ color: "#f5f7f1" }}>
              Тематика
              <HelpHint text={selectedDirection.description} />
            </label>
            <select
              className="form-input"
              value={contentDirection}
              onChange={(event) => setContentDirection(event.target.value as ContentDirection)}
            >
              {DIRECTION_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label form-label-inline" style={{ color: "#f5f7f1" }}>
              Каналы
              <HelpHint text="Генерация пойдёт только для отмеченных каналов." />
            </label>
            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
              {normalizedChannels.map((channel) => {
                const checked = selectedChannels.includes(channel);

                return (
                  <label
                    key={channel}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "8px",
                      padding: "10px 14px",
                      borderRadius: "999px",
                      border: checked ? "1px solid rgba(220, 255, 120, 0.55)" : "1px solid rgba(255, 255, 255, 0.1)",
                      background: checked ? "rgba(220, 255, 120, 0.12)" : "rgba(255,255,255,0.03)",
                      color: "#f5f7f1",
                      cursor: "pointer",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleChannel(channel)}
                      style={{ accentColor: "rgb(220, 255, 120)" }}
                    />
                    <span>{formatChannelLabel(channel)}</span>
                  </label>
                );
              })}
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label" style={{ color: "#f5f7f1" }}>
              Текст или тезисы
            </label>
            <textarea
              className="form-input"
              rows={10}
              placeholder="Готовый текст или короткий бриф"
              value={text}
              onChange={(event) => setText(event.target.value)}
              style={{ minHeight: "220px", maxHeight: "40vh", resize: "vertical" }}
            />
          </div>

          <div
            style={{
              display: "grid",
              gap: "10px",
              padding: "14px 16px",
              borderRadius: "14px",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              background: "rgba(255,255,255,0.03)",
            }}
          >
            <label
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "10px",
                color: "#f5f7f1",
                cursor: "pointer",
              }}
            >
              <input
                type="checkbox"
                checked={includeIllustration}
                onChange={(event) => setIncludeIllustration(event.target.checked)}
                style={{ accentColor: "rgb(220, 255, 120)" }}
              />
              <span style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
                <span>Пост пойдёт с иллюстрацией</span>
                <HelpHint text="Если включено, ИИ ужимает текст так, чтобы Telegram-пост с картинкой помещался в одну публикацию." />
              </span>
            </label>
          </div>

          {selectedChannels.length === 0 ? <div style={{ color: "#ffb366" }}>Выберите хотя бы один канал.</div> : null}
          {error ? <div style={{ color: "#ff8e8e" }}>{error}</div> : null}
        </div>

        <div
          style={{
            flexShrink: 0,
            display: "flex",
            justifyContent: "flex-end",
            gap: "12px",
            flexWrap: "wrap",
            padding: "16px 24px 24px",
            borderTop: "1px solid rgba(255, 255, 255, 0.08)",
            background: "#101114",
          }}
        >
          <button type="button" className="btn" disabled={!canSave} onClick={() => void handleSubmit(false)}>
            {isSubmitting === "save" ? "Добавляем..." : "Добавить в план"}
          </button>
          <HelpHint text="Сохраняет новый материал как черновик из вашего готового текста." />
          <button type="button" className="btn btn-primary" disabled={!canGenerate} onClick={() => void handleSubmit(true)}>
            {isSubmitting === "generate" ? "Генерируем пост..." : "Сгенерировать пост"}
          </button>
          <HelpHint text="Использует тезисы как бриф, пишет заголовок и текст через ИИ, затем кладёт результат в план." />
        </div>
      </div>
    </div>
  ) : null;

  return (
    <>
      <button type="button" className="btn btn-primary" onClick={() => setIsOpen(true)}>
        Написать пост
      </button>
      {mounted && modal ? createPortal(modal, document.body) : null}
    </>
  );
}
