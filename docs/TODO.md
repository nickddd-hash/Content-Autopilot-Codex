# TODO

## Now

Current focus additions:

- Add manual date editing for scheduled posts from plan or item page
- Add a clearer monthly calendar experience on the plan page
- Recheck Telegram publication flow after automatic shortening of plan-generated drafts
- Make publishable length constraints visible earlier in the editing flow, not only at publish time

- Сделать на уровне плана действие, которое генерирует не только темы, но и сами материалы по всему плану
- Превратить текущий flow в более автоматический: тема -> пост -> иллюстрация без ручного клика по каждому item
- Ещё сильнее упростить страницу плана и убрать остаточные лишние состояния

## Product UX

- Добавить более явный flow для “материал готов, можно публиковать”
- Продумать кнопку уровня плана вроде `Собрать материалы`
- Сделать более понятный переход от плана к публикации
- Привести оставшиеся экраны к чистому русскому UI без артефактов кодировки

## Automation

- Реализовать настоящий автопостинг:
  - система сама собирает темы
  - система сама генерирует материалы
  - система сама публикует по расписанию
- Сохранить возможность ручного редактирования и удаления материалов даже в автопилоте

## Plan Intelligence

- Добавить персонажей-проверяющих для оценки плана
- Базовые роли для старта:
  - обычный нетехнический читатель
  - предприниматель-фрилансер
  - эксперт / частная практика
  - владелец малого бизнеса
- На основе их оценок пересобирать или докручивать план
- Делать это на этапе финальной отладки, не раньше

## Security Follow-Up

- Ротировать внешние ключи провайдеров после инцидента:
  - OpenAI
  - KIE
  - другие сторонние API-ключи, если используются
- Отдельно пройтись по серверу на предмет признаков повторной компрометации
- При желании добавить ещё один уровень защиты:
  - fail2ban
  - docker hardening
  - отдельные Docker networks без лишней публикации портов

## Technical

- Нормализовать persistence для медиа, чтобы иллюстрации не зависели от пересборки контейнера
- При необходимости вынести публикацию и автогенерацию в фоновые задачи
- Держать серверный деплой как основное окружение, а localhost только для локальных правок
## Session 2026-04-23 Follow-Up

- Run live end-to-end OpenRouter text test after saving production settings.
- Run live end-to-end OpenRouter image regeneration test after saving production settings.
- If OpenRouter image results are good, decide whether to keep OpenAI only as fallback.
- Add clearer settings/help text so it is obvious that provider choice affects both text and image generation.

## Session 2026-04-24 Follow-Up

- Finish the content plan page redesign:
  - compact current-month + next-month calendar on the left
  - selected-day post list on the right
  - no date editing controls inside the plan page
- Keep item page as the single place for:
  - date changes
  - editing
  - regenerate text
  - regenerate image
  - publish now
- Recheck the live rendered plan page after the calendar redesign and verify there are no encoding regressions.
- Keep future UI cleanup point-sized; avoid broad file rewrites on plan/item routes.
