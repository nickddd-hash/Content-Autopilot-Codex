export const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api";

export async function fetchJson<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${apiBaseUrl}${path}`, {
      cache: "no-store",
    });

    if (!response.ok) {
      console.error(`API Error ${response.status} for ${path}`);
      return fallback;
    }

    return (await response.json()) as T;
  } catch (err) {
    console.error(`Fetch failed for ${path}:`, err);
    return fallback;
  }
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function patchJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: "Черновик",
    planned: "Запланировано",
    "review-ready": "Готово к ревью",
    published: "Опубликовано",
    failed: "Ошибка",
    active: "Активен",
    running: "В работе",
    completed: "Завершено",
  };

  return labels[status] || status;
}
