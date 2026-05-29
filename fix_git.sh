#!/bin/bash

echo "=== Исправление Git конфигурации ==="

# Отключаем GPG подпись
git config --global commit.gpgsign false

# Пробуем получить email из GitHub API
if [ -n "$GITHUB_TOKEN" ]; then
    EMAIL=$(curl -s https://api.github.com/user/emails -H "Authorization: Bearer $GITHUB_TOKEN" 2>/dev/null | grep -o '"email":"[^"]*"' | head -1 | cut -d'"' -f4)
fi

# Если не получилось — запрашиваем вручную
if [ -z "$EMAIL" ]; then
    echo "Не удалось автоматически определить email"
    echo "Ваш приватный email GitHub (виден в Settings → Emails):"
    echo "Обычно это: ваш-логин@users.noreply.github.com"
    read -p "Введите email: " EMAIL
fi

# Устанавливаем имя (измените на своё)
git config --global user.name "Akil Ibrahim"

# Устанавливаем email
git config --global user.email "$EMAIL"

# Показываем результат
echo ""
echo "=== Текущие настройки ==="
git config --global user.name | cat
git config --global user.email | cat
echo "commit.gpgsign = $(git config --global commit.gpgsign)"

# Делаем коммит
echo ""
echo "=== Делаем коммит ==="
git add .
git commit -m "refactoring"

# Пушим
echo ""
echo "=== Пушим ==="
git push

echo ""
echo "=== Готово ==="
