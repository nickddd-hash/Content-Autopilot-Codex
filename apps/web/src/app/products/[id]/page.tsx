import { fetchJson, postJson } from "@/lib/api";
import Link from "next/link";
import { revalidatePath } from "next/cache";

async function addChannelAction(formData: FormData) {
  "use server";
  const productId = String(formData.get("productId"));
  const platform = String(formData.get("platform"));
  const name = String(formData.get("name"));
  
  await postJson(`/products/${productId}/channels`, {
    platform,
    name,
    credentials: {}
  });
  
  revalidatePath(`/products/${productId}`);
}

async function addSourceAction(formData: FormData) {
  "use server";
  const productId = String(formData.get("productId"));
  const platform = String(formData.get("platform"));
  const sourceUrl = String(formData.get("sourceUrl"));
  const sourceType = String(formData.get("sourceType"));
  
  await postJson(`/monitoring-sources`, {
    product_id: productId,
    platform,
    source_url: sourceUrl,
    source_type: sourceType,
    is_active: true
  });
  
  revalidatePath(`/products/${productId}`);
}

async function updateProductContextAction(formData: FormData) {
  "use server";
  const productId = String(formData.get("productId"));
  const fullDescription = String(formData.get("fullDescription") || "");
  const toneOfVoice = String(formData.get("toneOfVoice") || "");
  const targetAudience = String(formData.get("targetAudience") || "");
  
  await patchJson(`/products/${productId}`, {
    full_description: fullDescription,
    tone_of_voice: toneOfVoice,
    target_audience: targetAudience
  });
  
  revalidatePath(`/products/${productId}`);
}

export default async function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = await params;
  const productId = resolvedParams.id;
  const product = await fetchJson<any>(`/products/${productId}`, null);

  if (!product) {
    return <div className="empty-state">Product not found.</div>;
  }

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">Продукт</p>
          <h1>{product.name}</h1>
          <p className="lead">{product.short_description || "Управление каналами дистрибуции и мониторинга."}</p>
        </div>
      </header>

      <section className="panel-grid">
        <article className="panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">Дистрибуция</span>
              <h2 className="panel-title">Каналы</h2>
            </div>
          </div>
          
          <div style={{ marginBottom: "24px", padding: "16px", background: "rgba(255,255,255,0.02)", borderRadius: "16px", border: "1px dashed var(--border)" }}>
            <form action={addChannelAction} style={{ display: "flex", gap: "12px", alignItems: "flex-end", flexWrap: "wrap" }}>
              <input type="hidden" name="productId" value={productId} />
              <div style={{ flex: 1, minWidth: "150px" }}>
                <label className="form-label">Платформа</label>
                <select name="platform" className="form-select" required>
                  <option value="telegram">Telegram</option>
                  <option value="instagram">Instagram</option>
                  <option value="youtube">YouTube</option>
                  <option value="blog">Blog</option>
                </select>
              </div>
              <div style={{ flex: 2, minWidth: "200px" }}>
                <label className="form-label">Название канала</label>
                <input type="text" name="name" className="form-input" placeholder="Например: Health Concilium TG" required />
              </div>
              <button type="submit" className="btn btn-primary" style={{ height: "48px" }}>Добавить</button>
            </form>
          </div>

          <div className="list-container">
            {product.channels && product.channels.length > 0 ? (
              product.channels.map((channel: any) => (
                <div key={channel.id} className="list-item">
                  <div>
                    <span className="list-item-title">{channel.platform}</span>
                    <span className="list-item-sub">{channel.name}</span>
                  </div>
                  <span className="badge badge-success">Активен</span>
                </div>
              ))
            ) : (
              <div className="empty-state" style={{ padding: "30px 20px" }}>
                <strong>Нет каналов</strong>
                <p>Добавьте каналы дистрибуции выше.</p>
              </div>
            )}
          </div>
        </article>

        <article className="panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">Research</span>
              <h2 className="panel-title">Мониторинг конкурентов</h2>
            </div>
          </div>
          
          <div style={{ marginBottom: "24px", padding: "16px", background: "rgba(255,255,255,0.02)", borderRadius: "16px", border: "1px dashed var(--border)" }}>
            <form action={addSourceAction} style={{ display: "flex", gap: "12px", alignItems: "flex-end", flexWrap: "wrap" }}>
              <input type="hidden" name="productId" value={productId} />
              <div style={{ flex: 1, minWidth: "120px" }}>
                <label className="form-label">Платформа</label>
                <select name="platform" className="form-select" required>
                  <option value="instagram">Instagram</option>
                  <option value="telegram">Telegram</option>
                  <option value="youtube">YouTube</option>
                </select>
              </div>
              <div style={{ flex: 1, minWidth: "120px" }}>
                <label className="form-label">Тип</label>
                <select name="sourceType" className="form-select" required>
                  <option value="competitor_profile">Профиль</option>
                  <option value="hashtag">Хэштег</option>
                </select>
              </div>
              <div style={{ flex: 2, minWidth: "200px" }}>
                <label className="form-label">Ссылка / URL</label>
                <input type="text" name="sourceUrl" className="form-input" placeholder="https://instagram.com/..." required />
              </div>
              <button type="submit" className="btn btn-primary" style={{ height: "48px" }}>Добавить</button>
            </form>
          </div>

          <div className="list-container">
            {product.monitoring_sources && product.monitoring_sources.length > 0 ? (
              product.monitoring_sources.map((source: any) => (
                <div key={source.id} className="list-item">
                  <div>
                    <span className="list-item-title">{source.platform}</span>
                    <span className="list-item-sub">{source.source_url}</span>
                  </div>
                  <span className="badge badge-info">{source.source_type}</span>
                </div>
              ))
            ) : (
              <div className="empty-state" style={{ padding: "30px 20px" }}>
                <strong>Нет источников</strong>
                <p>Добавьте конкурентов или источники для мониторинга.</p>
              </div>
            )}
          </div>
        </article>
        <article className="panel panel-wide">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">База знаний</span>
              <h2 className="panel-title">Контекст и Стратегия продукта</h2>
            </div>
          </div>
          <form action={updateProductContextAction} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            <input type="hidden" name="productId" value={productId} />
            
            <div className="form-group">
              <label className="form-label" style={{ display: "flex", justifyContent: "space-between" }}>
                <span>Глубокий контекст (Резюме от Gemini)</span>
                <span className="badge badge-info" style={{ fontWeight: "normal" }}>full_description</span>
              </label>
              <p className="form-hint" style={{ marginBottom: "8px", fontSize: "13px", color: "var(--muted)" }}>
                Вставьте сюда результаты анализа ваших навыков, проектов и экспертизы. AI-агент будет читать это перед каждой генерацией текста.
              </p>
              <textarea 
                name="fullDescription" 
                className="form-input" 
                rows={8} 
                placeholder="Вставьте глубокий контекст о проекте или вашем личном бренде..."
                defaultValue={product.full_description || ""}
              />
            </div>

            <div className="form-group" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
              <div>
                <label className="form-label">Голос и Тон (Tone of Voice)</label>
                <p className="form-hint" style={{ marginBottom: "8px", fontSize: "13px", color: "var(--muted)" }}>
                  Как общаться с аудиторией? (Например: "Пиши дерзко, без воды, обращайся на 'ты'")
                </p>
                <textarea 
                  name="toneOfVoice" 
                  className="form-input" 
                  rows={4} 
                  placeholder="Опишите стиль..."
                  defaultValue={product.tone_of_voice || ""}
                />
              </div>
              
              <div>
                <label className="form-label">Целевая Аудитория</label>
                <p className="form-hint" style={{ marginBottom: "8px", fontSize: "13px", color: "var(--muted)" }}>
                  Для кого мы пишем этот контент?
                </p>
                <textarea 
                  name="targetAudience" 
                  className="form-input" 
                  rows={4} 
                  placeholder="Опишите портрет аудитории..."
                  defaultValue={product.target_audience || ""}
                />
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "12px" }}>
              <button type="submit" className="btn btn-primary" style={{ padding: "0 32px" }}>
                Сохранить контекст
              </button>
            </div>
          </form>
        </article>
      </section>
    </>
  );
}
