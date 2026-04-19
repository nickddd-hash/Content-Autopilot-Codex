import { postJson } from "@/lib/api";
import Link from "next/link";
import { redirect } from "next/navigation";

const cyrillicToLatinMap: Record<string, string> = {
  'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh',
  'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
  'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts',
  'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu',
  'я': 'ya'
};

function transliterate(text: string): string {
  return text.toLowerCase().split('').map(char => cyrillicToLatinMap[char] || char).join('');
}

async function createProductAction(formData: FormData) {
  "use server";
  const name = String(formData.get("name"));
  
  // Автоматическая генерация slug из названия с транслитерацией
  let slug = transliterate(name)
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");

  if (!slug) {
    slug = `project-${Date.now()}`;
  }

  const product = await postJson<any>("/products", {
    name,
    slug,
  });

  if (product && product.id) {
    redirect(`/products/${product.id}`);
  } else {
    // В случае ошибки возвращаем на главную
    redirect("/");
  }
}

export default function NewProductPage() {
  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">Новый проект</p>
          <h1>Создание продукта</h1>
          <p className="lead">Введите название вашего продукта или бренда, чтобы создать рабочее пространство.</p>
        </div>
      </header>
      
      <section className="panel-grid" style={{ gridTemplateColumns: "1fr" }}>
        <article className="panel" style={{ maxWidth: "600px" }}>
          <div className="panel-header" style={{ marginBottom: "24px" }}>
             <h2 className="panel-title">Детали продукта</h2>
          </div>
          <form action={createProductAction}>
            <div className="form-group">
              <label className="form-label">Название</label>
              <input 
                type="text" 
                name="name" 
                className="form-input" 
                placeholder="Например: Health Concilium" 
                required 
                autoFocus
              />
            </div>
            
            <div style={{ display: "flex", gap: "12px", marginTop: "32px" }}>
              <button type="submit" className="btn btn-primary">Создать продукт</button>
              <Link href="/" className="btn">Отмена</Link>
            </div>
          </form>
        </article>
      </section>
    </>
  );
}
