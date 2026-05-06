import Link from "next/link";
import { fetchJson } from "@/lib/api";
import ProductPlanForm from "../ProductPlanForm";

type NewPlanPageProps = {
  params: Promise<{ id: string }>;
};

type ProductSummary = {
  id: string;
  name: string;
};

export default async function NewPlanPage({ params }: NewPlanPageProps) {
  const { id: productId } = await params;

  const product = await fetchJson<ProductSummary | null>(`/products/${productId}`, null);

  if (!product) {
    return <div className="empty-state">Продукт не найден.</div>;
  }

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">
            <Link href={`/products/${productId}`} style={{ textDecoration: "none", color: "var(--text-muted)" }}>
              {product.name}
            </Link>
            {" / Новый план"}
          </p>
          <h1>Создать контент-план</h1>
          <p className="lead">Настройте параметры и нажмите «Создать план» — темы сгенерируете внутри плана.</p>
        </div>
      </header>

      <section style={{ maxWidth: "640px" }}>
        <article className="panel">
          <ProductPlanForm productId={productId} />
        </article>
      </section>
    </>
  );
}
