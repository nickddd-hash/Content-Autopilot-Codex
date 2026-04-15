const cards = [
  {
    title: "Автопилот",
    description: "Система будет сама планировать, генерировать и публиковать контент.",
  },
  {
    title: "Продукты",
    description: "У каждого продукта будут свои аудитории, офферы, правила и каналы публикации.",
  },
  {
    title: "Контроль",
    description: "Ручное участие остается только для редких ошибок и перегенерации.",
  },
];

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero">
        <p className="eyebrow">Olympus Athena</p>
        <h1>Личный AI-автопилот для продвижения ваших продуктов</h1>
        <p className="lead">
          Этот проект собирается как рабочий инструмент: минимум ручного контроля,
          максимум автоматической генерации, планирования и публикации.
        </p>
      </section>

      <section className="card-grid">
        {cards.map((card) => (
          <article key={card.title} className="card">
            <h2>{card.title}</h2>
            <p>{card.description}</p>
          </article>
        ))}
      </section>
    </main>
  );
}

