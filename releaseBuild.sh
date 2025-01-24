#!/bin/bash

# Create dist directory
mkdir -p dist/{x86_64,aarch64,armhf}

# Архитектуры для сборки
ARCHS=("x86_64" "aarch64" "armhf")

# Создаем папки для архитектур
for arch in "${ARCHS[@]}"; do
    mkdir -p "dist/$arch"
    
    # Собираем под текущую архитектуру
    python3 -m nuitka \
        --standalone \
        --plugin-enable=pyqt6 \
        --include-data-dir=icons=icons \
        --include-data-dir=images=images \
        --include-data-dir=fonts=fonts \
        --output-dir="dist/$arch" \
        --target-arch="$arch" \
        main.py
        
    # Создаем архив
    cd dist
    tar -czf "RytonStudio-$arch.tar.gz" "$arch"/*
    cd ..
done
