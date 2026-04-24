"use client";

import { useMemo, useState, useTransition } from "react";

import HelpHint from "@/components/HelpHint";

type ProductChannel = {
  id: string;
  platform: string;
  name: string;
  settings_json: Record<string, string>;
  external_id: string | null;
  external_name: string | null;
  validation_status: string;
  validation_message: string | null;
  validated_at: string | null;
  is_active: boolean;
  configured_secret_keys: string[];
};

type ProductChannelsPanelProps = {
  productId: string;
  initialChannels: ProductChannel[];
};

type PlatformKey = "telegram" | "vk";

type PlatformConfig = {
  label: string;
  defaultName: string;
  secrets: Array<{ key: string; label: string; type?: string; placeholder: string }>;
  settings: Array<{ key: string; label: string; placeholder: string }>;
};

const PLATFORM_CONFIGS: Record<PlatformKey, PlatformConfig> = {
  telegram: {
    label: "Telegram",
    defaultName: "Telegram",
    secrets: [{ key: "bot_token", label: "Bot token", type: "password", placeholder: "123456:AAF..." }],
    settings: [{ key: "chat_id", label: "Chat ID", placeholder: "@channel_name или -100..." }],
  },
  vk: {
    label: "VK",
    defaultName: "VK",
    secrets: [{ key: "access_token", label: "Access token", type: "password", placeholder: "vk1.a...." }],
    settings: [{ key: "group_id", label: "Group ID", placeholder: "123456789" }],
  },
};

function badgeLabel(status: string) {
  if (status === "valid") return "Связь есть";
  if (status === "invalid") return "Ошибка связи";
  return "Не проверено";
}

function badgeClass(status: string) {
  if (status === "valid") return "badge badge-success";
  if (status === "invalid") return "badge badge-danger";
  return "badge badge-outline";
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // ignore parse errors
    }
    throw new Error(detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export default function ProductChannelsPanel({ productId, initialChannels }: ProductChannelsPanelProps) {
  const [channels, setChannels] = useState(initialChannels);
  const [platform, setPlatform] = useState<PlatformKey>("telegram");
  const [name, setName] = useState(PLATFORM_CONFIGS.telegram.defaultName);
  const [secrets, setSecrets] = useState<Record<string, string>>({ bot_token: "" });
  const [settings, setSettings] = useState<Record<string, string>>({ chat_id: "" });
  const [error, setError] = useState<string | null>(null);
  const [pendingText, setPendingText] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const platformConfig = PLATFORM_CONFIGS[platform];
  const existingChannel = useMemo(
    () => channels.find((channel) => channel.platform === platform),
    [channels, platform],
  );
  const isPlatformLocked = existingChannel?.validation_status === "valid";

  function switchPlatform(nextPlatform: PlatformKey) {
    const config = PLATFORM_CONFIGS[nextPlatform];
    const channel = channels.find((item) => item.platform === nextPlatform);
    setPlatform(nextPlatform);
    setName(channel?.name || config.defaultName);
    setSecrets(Object.fromEntries(config.secrets.map((field) => [field.key, ""])));
    setSettings(
      Object.fromEntries(config.settings.map((field) => [field.key, String(channel?.settings_json?.[field.key] ?? "")])),
    );
    setError(null);
  }

  function updateSecret(key: string, value: string) {
    setSecrets((current) => ({ ...current, [key]: value }));
  }

  function updateSetting(key: string, value: string) {
    setSettings((current) => ({ ...current, [key]: value }));
  }

  function resetForm() {
    switchPlatform(platform);
  }

  function handleCreateChannel() {
    setError(null);
    setPendingText(existingChannel ? "Обновляем канал..." : "Подключаем канал...");

    startTransition(async () => {
      try {
        const payload = {
          name: name.trim() || platformConfig.defaultName,
          secrets,
          settings,
        };
        const saved = existingChannel
          ? await requestJson<ProductChannel>(`/api/products/${productId}/channels/${existingChannel.id}`, {
              method: "PATCH",
              body: JSON.stringify(payload),
            })
          : await requestJson<ProductChannel>(`/api/products/${productId}/channels`, {
              method: "POST",
              body: JSON.stringify({
                platform,
                ...payload,
              }),
            });

        const validated = await requestJson<ProductChannel>(`/api/products/${productId}/channels/${saved.id}/validate`, {
          method: "POST",
        });

        setChannels((current) => {
          const exists = current.some((channel) => channel.id === validated.id);
          return exists ? current.map((channel) => (channel.id === validated.id ? validated : channel)) : [...current, validated];
        });
        resetForm();
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "Не удалось сохранить данные канала.");
      } finally {
        setPendingText(null);
      }
    });
  }

  function handleValidateChannel(channelId: string) {
    setError(null);
    setPendingText("Проверяем связь...");

    startTransition(async () => {
      try {
        const validated = await requestJson<ProductChannel>(`/api/products/${productId}/channels/${channelId}/validate`, {
          method: "POST",
        });
        setChannels((current) => current.map((channel) => (channel.id === channelId ? validated : channel)));
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "Не удалось проверить связь.");
      } finally {
        setPendingText(null);
      }
    });
  }

  function handleDeleteChannel(channelId: string, channelName: string) {
    const confirmed = window.confirm(
      `Удалить канал "${channelName}"?\n\nПосле удаления нужно будет пересмотреть контент-план: часть материалов и автопостинг могли быть рассчитаны на этот канал.`,
    );
    if (!confirmed) return;

    const secondConfirmed = window.confirm("Точно удалить канал и отключить его от проекта?");
    if (!secondConfirmed) return;

    setError(null);
    setPendingText("Удаляем канал...");

    startTransition(async () => {
      try {
        await requestJson<void>(`/api/products/${productId}/channels/${channelId}`, {
          method: "DELETE",
        });
        setChannels((current) => current.filter((channel) => channel.id !== channelId));
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "Не удалось удалить канал.");
      } finally {
        setPendingText(null);
      }
    });
  }

  return (
    <>
      <div className="panel-header">
        <div>
          <span className="panel-kicker">Дистрибуция</span>
          <h2 className="panel-title" style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
            Каналы
            <HelpHint text="Подключайте только реальные каналы проекта. После добавления система сразу проверяет secrets и связь с каналом." />
          </h2>
        </div>
        <span className="badge badge-accent">{channels.length}</span>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1.1fr 1fr 1fr auto",
          gap: "12px",
          alignItems: "end",
          marginBottom: "14px",
        }}
      >
        <label style={{ display: "grid", gap: "8px" }}>
          <span className="form-label">Платформа</span>
          <select className="form-select" value={platform} onChange={(event) => switchPlatform(event.target.value as PlatformKey)} disabled={isPending}>
            {Object.entries(PLATFORM_CONFIGS).map(([key, config]) => (
              <option key={key} value={key}>
                {config.label}
              </option>
            ))}
          </select>
        </label>

        <label style={{ display: "grid", gap: "8px" }}>
          <span className="form-label">Название</span>
          <input className="form-input" value={name} onChange={(event) => setName(event.target.value)} disabled={isPending} />
        </label>

        {platformConfig.secrets.map((field) => (
          <label key={field.key} style={{ display: "grid", gap: "8px" }}>
            <span className="form-label">{field.label}</span>
            <input
              className="form-input"
              type={field.type || "text"}
              placeholder={field.placeholder}
              value={secrets[field.key] ?? ""}
              onChange={(event) => updateSecret(field.key, event.target.value)}
              disabled={isPending}
            />
          </label>
        ))}

        {platformConfig.settings.map((field) => (
          <label key={field.key} style={{ display: "grid", gap: "8px" }}>
            <span className="form-label">{field.label}</span>
            <input
              className="form-input"
              placeholder={field.placeholder}
              value={settings[field.key] ?? ""}
              onChange={(event) => updateSetting(field.key, event.target.value)}
              disabled={isPending}
            />
          </label>
        ))}

        <button type="button" className="btn btn-primary" onClick={handleCreateChannel} disabled={isPending || isPlatformLocked}>
          {pendingText || (existingChannel ? "Подключить заново" : "Подключить")}
        </button>
      </div>

      {existingChannel?.validation_status === "invalid" ? (
        <div className="empty-state compact-empty-state" style={{ marginBottom: "14px", borderColor: "rgba(180, 52, 52, 0.18)" }}>
          <strong>Связь не установлена</strong>
        </div>
      ) : null}

      {existingChannel?.validation_status === "valid" ? (
        <div className="empty-state compact-empty-state" style={{ marginBottom: "14px" }}>
          <strong>Канал уже подключён</strong>
        </div>
      ) : null}

      {error ? (
        <div className="empty-state compact-empty-state" style={{ borderColor: "rgba(180, 52, 52, 0.24)", color: "var(--danger)", marginBottom: "14px" }}>
          <strong>Не получилось</strong>
          <p>{error}</p>
        </div>
      ) : null}

      <div className="list-container">
        {channels.length > 0 ? (
          channels.map((channel) => (
            <div key={channel.id} className="list-item compact-list-item" style={{ alignItems: "flex-start", gap: "16px" }}>
              <div style={{ display: "grid", gap: "8px" }}>
                <div>
                  <span className="list-item-title">{channel.name}</span>
                  <span className="list-item-sub">
                    {PLATFORM_CONFIGS[channel.platform as PlatformKey]?.label || channel.platform}
                    {channel.external_name ? ` · ${channel.external_name}` : ""}
                  </span>
                </div>
                <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                  {channel.configured_secret_keys.map((secretKey) => (
                    <span key={secretKey} className="badge badge-outline">
                      {secretKey}
                    </span>
                  ))}
                </div>
                {channel.validation_message ? (
                  <p className="form-hint" style={{ margin: 0 }}>
                    {channel.validation_message}
                  </p>
                ) : null}
              </div>

              <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", justifyContent: "flex-end", marginLeft: "auto" }}>
                <span className={badgeClass(channel.validation_status)}>{badgeLabel(channel.validation_status)}</span>
                <button type="button" className="btn btn-sm" onClick={() => handleValidateChannel(channel.id)} disabled={isPending}>
                  Проверить связь
                </button>
                <button
                  type="button"
                  className="btn btn-sm"
                  style={{ borderColor: "var(--danger)", color: "var(--danger)" }}
                  onClick={() => handleDeleteChannel(channel.id, channel.name)}
                  disabled={isPending}
                >
                  Удалить канал
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="empty-state compact-empty-state">
            <strong>Каналы пока не подключены</strong>
          </div>
        )}
      </div>
    </>
  );
}
