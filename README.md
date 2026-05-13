# Restaurant Management System

![CI](https://github.com/Dev66-66/LAB12/actions/workflows/ci.yml/badge.svg)
![Coverage](https://codecov.io/gh/Dev66-66/LAB12/branch/main/graph/badge.svg)

**ФИО:** Фомичев Ярослав Николаевич

**Группа:** 221131

**Вариант:** 21

**Лабораторная работа:** №12

---

## AI Code Review

Репозиторий подключён к автоматическому code review на базе **Claude claude-sonnet-4-6** (Anthropic).  
При каждом создании или обновлении Pull Request, затрагивающего файлы в `app/` или `tests/`,  
GitHub Actions запускает workflow `.github/workflows/ai_review.yml`, который:

1. Получает `git diff` между веткой PR и базовой веткой (`main`/`master`).
2. Отправляет diff в Claude API с запросом провести code review.
3. Публикует ответ Claude как комментарий прямо в Pull Request.

Пример структуры автоматического комментария:

```
## 🤖 AI Code Review

### 🐛 Возможные баги
...

### 🔒 Безопасность
...

### ⚡ Производительность
...

### 📝 Стиль и PEP 8
...

### ✅ Хорошие практики
...

### 📋 Итог
...

---
*Автоматическое ревью от Claude. Результаты носят рекомендательный характер.*
```

### Как настроить ANTHROPIC_API_KEY

1. Получите API-ключ на [console.anthropic.com](https://console.anthropic.com).
2. Откройте репозиторий на GitHub.
3. Перейдите в **Settings → Secrets and variables → Actions → New repository secret**.
4. Создайте секрет с именем `ANTHROPIC_API_KEY` и вставьте ключ в поле Value.
5. Сохраните. Все последующие PR будут автоматически проходить AI-ревью.

> **Скриншот:** после создания первого Pull Request в репозитории здесь появится  
> снимок экрана с примером комментария от Claude в разделе PR → Comments.
