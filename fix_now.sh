#!/bin/bash

echo "=== Принудительное исправление ==="

# 1. Полностью отключаем GPG (разными способами на всякий случай)
git config --global commit.gpgsign false
git config --local commit.gpgsign false 2>/dev/null
unset GPG_TTY
unset GPG_AGENT_INFO

# 2. Устанавливаем email (укажите свой! Замените логин)
git config --global user.name "Akil Ibrahim"
git config --global user.email "Akil-Ibrahim@users.noreply.github.com"

# 3. Проверяем
echo ""
echo "=== ПРОВЕРКА ==="
echo "Имя: $(git config --global user.name)"
echo "Email: $(git config --global user.email)"
echo "GPG: $(git config --global commit.gpgsign)"
echo ""

# 4. Делаем коммит без подписи
echo "=== КОММИТ ==="
git add .
git commit -m "refactoring" --no-gpg-sign

# 5. Пуш
echo ""
echo "=== ПУШ ==="
git push

echo ""
echo "=== ГОТОВО ==="
