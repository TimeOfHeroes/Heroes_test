#!/usr/bin/env python3
"""
Скрипт для скачивания и оптимизации изображений из Baserow
"""

import csv
import os
import re
import hashlib
import requests
from PIL import Image
from io import BytesIO
import time

# Папки
IMAGE_CACHE_DIR = 'images_cache'
CSV_FILES = [
    'heroes.csv',
    'export - Герои - View.csv',
    'item_images.csv'
]

def extract_url(text):
    """Извлекает URL из строки вида 'name.png (https://...)'"""
    if not text:
        return None
    
    # Ищем URL в скобках
    match = re.search(r'\((https?://[^)]+)\)', text)
    if match:
        return match.group(1)
    
    # Ищем прямую ссылку
    match = re.search(r'https?://[^\s,)]+', text)
    if match:
        return match.group(0)
    
    return None

def get_image_hash(url):
    """Создает хеш из URL для кеширования"""
    return hashlib.md5(url.encode()).hexdigest()[:16]

def download_and_optimize_image(url, filename, max_width=400, quality=80):
    """Скачивает и оптимизирует изображение"""
    
    if not url:
        return None
    
    # Путь к файлу в кеше
    cache_file = os.path.join(IMAGE_CACHE_DIR, filename)
    
    # Проверяем, есть ли уже оптимизированная версия
    if os.path.exists(cache_file):
        return cache_file
    
    try:
        # Скачиваем изображение
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Открываем изображение
        img = Image.open(BytesIO(response.content))
        
        # Конвертируем в RGB если нужно (для PNG с прозрачностью)
        if img.mode in ('RGBA', 'LA'):
            # Сохраняем альфа-канал для PNG
            img.save(cache_file, 'PNG', optimize=True)
        else:
            # Для JPEG - сжимаем
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Изменяем размер, если нужно
            if max_width and img.width > max_width:
                ratio = max_width / img.width
                new_size = (max_width, int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Сохраняем с оптимизацией
            img.save(cache_file, 'JPEG', quality=quality, optimize=True)
        
        print(f'✅ Оптимизировано: {filename} ({os.path.getsize(cache_file)} байт)')
        return cache_file
        
    except Exception as e:
        print(f'❌ Ошибка для {filename}: {e}')
        return None

def process_csv_file(csv_path):
    """Обрабатывает CSV файл и извлекает URL изображений"""
    
    if not os.path.exists(csv_path):
        print(f'⚠️ Файл не найден: {csv_path}')
        return []
    
    urls = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Проверяем все колонки на наличие ссылок на картинки
            for key, value in row.items():
                if 'Картинка' in key or 'image' in key.lower() or 'icon' in key.lower():
                    url = extract_url(value)
                    if url:
                        # Создаем имя файла из хеша
                        file_hash = get_image_hash(url)
                        # Определяем расширение
                        ext = '.jpg'
                        if '.png' in url.lower() or 'png' in key.lower():
                            ext = '.png'
                        elif '.svg' in url.lower():
                            ext = '.svg'
                        
                        filename = f'{file_hash}{ext}'
                        urls.append((url, filename))
    
    return urls

def main():
    print('🚀 Запуск оптимизации изображений...')
    
    # Создаем папку для кеша
    os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)
    
    all_urls = []
    
    # Обрабатываем все CSV файлы
    for csv_file in CSV_FILES:
        print(f'📄 Обработка: {csv_file}')
        urls = process_csv_file(csv_file)
        all_urls.extend(urls)
        print(f'   Найдено URL: {len(urls)}')
    
    # Удаляем дубликаты
    unique_urls = list(set(all_urls))
    print(f'\n📊 Всего уникальных изображений: {len(unique_urls)}')
    
    # Скачиваем и оптимизируем
    success_count = 0
    for i, (url, filename) in enumerate(unique_urls, 1):
        print(f'[{i}/{len(unique_urls)}] Загрузка: {filename}')
        result = download_and_optimize_image(url, filename)
        if result:
            success_count += 1
        time.sleep(0.1)  # Небольшая задержка между запросами
    
    print(f'\n✅ Готово! Оптимизировано: {success_count}/{len(unique_urls)} изображений')

if __name__ == '__main__':
    main()
