from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import BrandProfile, ContentPlan, ContentPlanItem, Product, ProductContentSettings
from app.schemas.bootstrap import BootstrapWorkspaceResponse


FIRST_PRODUCT_SLUG = "health-concilium"


def _seed_plan_items() -> list[ContentPlanItem]:
    return [
        ContentPlanItem(
            order=1,
            title="Почему люди тонут в советах о здоровье и не начинают действовать",
            angle="Объяснить проблему информационного хаоса и показать ценность персонального маршрута.",
            target_keywords=["здоровье", "информационный шум", "персональный маршрут"],
            article_type="educational",
            cta_type="soft",
            status="planned",
        ),
        ContentPlanItem(
            order=2,
            title="Как анализы, питание и сон складываются в одну систему, а не в разрозненные советы",
            angle="Показать, что здоровье нельзя собирать по кускам из несвязанных рекомендаций.",
            target_keywords=["анализы", "питание", "сон", "системный подход"],
            article_type="educational",
            cta_type="soft",
            status="planned",
        ),
        ContentPlanItem(
            order=3,
            title="5 ежедневных сигналов, что организму нужен не контент, а понятный следующий шаг",
            angle="Сделать материал, который легко адаптируется в post, carousel и reel script.",
            target_keywords=["ежедневные привычки", "следующий шаг", "сигналы организма"],
            article_type="checklist",
            cta_type="soft",
            status="planned",
        ),
        ContentPlanItem(
            order=4,
            title="Чем персональный health-консьерж отличается от хаотичного поиска советов в интернете",
            angle="Аккуратно подвести к продуктовой логике без агрессивного продающего давления.",
            target_keywords=["health concierge", "персональные рекомендации", "поддержка"],
            article_type="comparison",
            cta_type="soft",
            status="planned",
        ),
    ]


async def bootstrap_first_workspace(session: AsyncSession) -> BootstrapWorkspaceResponse:
    now = datetime.now(UTC)
    month_key = now.strftime("%Y-%m")

    product_statement = (
        select(Product)
        .where(Product.slug == FIRST_PRODUCT_SLUG)
        .options(selectinload(Product.content_settings))
    )
    product = await session.scalar(product_statement)
    product_created = product is None

    if product is None:
        product = Product(
            name="Health Concilium",
            slug=FIRST_PRODUCT_SLUG,
            category="health",
            lifecycle_stage="mvp",
            short_description="Персональный цифровой советник по здоровью с ежедневной поддержкой и понятным маршрутом действий.",
            full_description=(
                "Health Concilium помогает человеку не теряться в противоречивой информации о здоровье, "
                "а получать понятный персональный маршрут по анализам, питанию, восстановлению, сну и ежедневным привычкам."
            ),
            target_audience=(
                "Взрослые люди, которые хотят системно заниматься здоровьем, но тонут в хаосе рекомендаций и не понимают следующий шаг."
            ),
            audience_segments=[
                "люди, которые хотят навести порядок в анализах и маркерах",
                "люди, которым нужен понятный маршрут по питанию, сну и восстановлению",
                "аудитория, которая устала от противоречивого health-контента",
            ],
            pain_points=[
                "слишком много противоречивых советов",
                "нет персонального маршрута и следующего шага",
                "сложно связать питание, анализы, сон и привычки в одну систему",
            ],
            value_proposition=(
                "Система превращает хаос советов о здоровье в персональный маршрут с понятными ежедневными действиями."
            ),
            key_features=[
                "персональный протокол",
                "консилиум врачей-агентов",
                "ежедневная поддержка",
                "понятный следующий шаг",
            ],
            content_pillars=[
                "питание",
                "сон",
                "восстановление",
                "анализы и маркеры",
                "привычки",
                "женское и метаболическое здоровье",
            ],
            strategic_goals=[
                "создать доверие через полезный образовательный контент",
                "объяснить продуктовую ценность без агрессивных продаж",
                "превращать внимание в диалог и onboarding",
            ],
            primary_channels=["instagram", "telegram", "vk", "blog"],
            tone_of_voice="Спокойный, объясняющий, человеческий, без инфошума и паники.",
            cta_strategy="Мягко подводить к следующему шагу: консультации, мини-диалог, разбор ситуации, onboarding в продукт.",
            website_url="https://hc.flowsmart.ru",
            blog_base_url="https://hc.flowsmart.ru/blog",
            is_active=True,
        )
        product.content_settings = ProductContentSettings(
            autopilot_enabled=True,
            articles_per_month=8,
            publish_days=[1, 3, 5],
            publish_time_utc="07:00",
            preferred_article_types=["educational", "checklist", "comparison"],
            forbidden_topics=["диагностика без врача", "обещания чудесного исцеления"],
            forbidden_phrases=["гарантированно вылечит", "100% результат"],
            target_keywords=["здоровье", "анализы", "сон", "питание", "восстановление"],
            social_posting_enabled=True,
            carousel_enabled=True,
            default_theme="Понятный ежедневный маршрут к здоровью без информационного хаоса",
        )
        session.add(product)
        await session.flush()

    brand_profile = await session.scalar(select(BrandProfile).limit(1))
    brand_profile_created = brand_profile is None

    if brand_profile is None:
        brand_profile = BrandProfile(
            brand_name="Health Concilium",
            brand_summary=(
                "Персональный цифровой советник по здоровью: помогает соединить анализы, питание, сон, восстановление "
                "и ежедневные привычки в понятный маршрут."
            ),
            user_style_description="Объяснять спокойно и умно, без паники, без инфоцыганского нажима и без сухого врачебного канцелярита.",
            audience_notes=[
                "людям нужен не шум, а ясность",
                "важно говорить человеческим языком, но не примитивно",
                "контент должен снижать тревогу и давать следующий шаг",
            ],
            core_messages=[
                "здоровье — это система, а не набор случайных советов",
                "человеку нужен понятный маршрут, а не новая порция инфошума",
                "ежедневные действия важнее перегруза информацией",
            ],
            allowed_tone=["спокойный", "человечный", "объясняющий", "структурный"],
            disallowed_tone=["панический", "агрессивно-продающий", "менторский", "инфоцыганский"],
            anti_slop_rules=[
                "не писать обобщенный пустой мотивационный контент",
                "не копировать шаблонные клише про осознанность и энергию",
                "каждый материал должен давать практический смысл и следующий шаг",
            ],
            compliance_rules=[
                "не обещать диагноз или лечение",
                "не подменять врача",
                "не использовать категоричные медицинские обещания",
            ],
            cta_rules=[
                "CTA должен быть мягким и естественным",
                "не давить на страх",
                "вести к диалогу, разбору или onboarding, а не к жесткому сейлу",
            ],
            vocabulary_preferences=["понятный маршрут", "следующий шаг", "ежедневные действия", "система"],
            formatting_rules=[
                "писать короткими абзацами",
                "начинать с реальной боли или путаницы человека",
                "заканчивать понятным выводом или следующим шагом",
            ],
            channel_strategy={
                "instagram": "короткие объясняющие посты, карусели и reel scripts с ясным хуком",
                "telegram": "более личный и сопровождающий формат",
                "vk": "адаптированные образовательные посты и карусели",
                "blog": "более полные статьи с evergreen value",
            },
            image_style_rules=[
                "чистые и понятные визуалы без кликбейтной медицинской эстетики",
                "акцент на доверии, ясности и современном digital health образе",
            ],
        )
        session.add(brand_profile)
        await session.flush()

    plan_statement = (
        select(ContentPlan)
        .where(ContentPlan.product_id == product.id, ContentPlan.month == month_key)
        .options(selectinload(ContentPlan.items))
    )
    content_plan = await session.scalar(plan_statement)
    content_plan_created = content_plan is None

    if content_plan is None:
        content_plan = ContentPlan(
            product_id=product.id,
            month=month_key,
            theme="Система здоровья без информационного хаоса",
            status="draft",
        )
        content_plan.items = _seed_plan_items()
        session.add(content_plan)
        await session.flush()

    await session.commit()

    return BootstrapWorkspaceResponse(
        product_id=product.id,
        brand_profile_id=brand_profile.id,
        content_plan_id=content_plan.id,
        product_created=product_created,
        brand_profile_created=brand_profile_created,
        content_plan_created=content_plan_created,
        seeded_items_count=len(content_plan.items),
    )
