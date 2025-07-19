#!/bin/bash

echo "=== Fixing Import Issues ==="

git add -A
git commit -m "fix: corregir imports y sintaxis en archivos Python

- Eliminar import suelto al final de progress.py
- Mover import asyncio al principio de new_plan_handler.py
- Asegurar que todos los imports estén correctamente ubicados

Esto soluciona posibles errores de importación al iniciar el bot."

git push origin main

echo "Fixes pushed! Ahora en el servidor ejecutá:"
echo "cd /root/nutrition-bot"
echo "git pull origin main"
echo "docker-compose restart telegram_bot"