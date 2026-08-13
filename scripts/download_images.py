#!/usr/bin/env python3
"""
Упрощённый скрипт для скачивания изображений
"""

import csv
import os
import re
import hashlib
import requests
import time

IMAGE_CACHE_DIR = 'images_cache'

# Поля, в которых могут быть ссылки на картинки
IMAGE_FIELDS = [
    'Картинка',
    'Картинка активная',
    'Картинка неактивная',
    'image',
    'icon'
]

def extract_url(text):
    """Извлекает URL из строки"""
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

def download_image(url, filename):
    """Скачивает изображение без оптимизации"""
    if not url:
        return None
    
    cache_file = os.path.join(IMAGE_CACHE_DIR, filename)
    
    if os.path.exists(cache_file):
        print(f'⏭️ Пропускаем (уже есть): {filename}')
        return cache_file
    
    try:
        print(f'⬇️ Скачиваем: {filename}')
        response = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        
        with open(cache_file, 'wb') as f:
            f.write(response.content)
        
        size_kb = os.path.getsize(cache_file) // 1024
        print(f'✅ Сохранён: {filename} ({size_kb} КБ)')
        return cache_file
        
    except Exception as e:
        print(f'❌ Ошибка для {filename}: {e}')
        return None

def process_csv_file(csv_path):
    """Обрабатывает CSV файл"""
    if not os.path.exists(csv_path):
        print(f'⚠️ Файл не найден: {csv_path}')
        return []
    
    urls = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                for field in IMAGE_FIELDS:
                    if field in row and row[field]:
                        url = extract_url(row[field])
                        if url:
                            file_hash = hashlib.md5(url.encode()).hexdigest()[:16]
                            ext = '.jpg'
                            if '.png' in url.lower():
                                ext = '.png'
                            elif '.svg' in url.lower():
                                ext = '.svg'
                            filename = f'{file_hash}{ext}'
                            urls.append((url, filename))
    except Exception as e:
        print(f'❌ Ошибка при чтении {csv_path}: {e}')
    
    return urls

def main():
    print('🚀 Запуск загрузки изображений...')
    print(f'📂 Рабочая папка: {os.getcwd()}')
    
    os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)
    
    CSV_FILES = ['heroes.csv', 'item_images.csv', 'Talent_description.csv']
    
    all_urls = []
    for csv_file in CSV_FILES:
        print(f'\n📄 Обработка: {csv_file}')
        urls = process_csv_file(csv_file)
        all_urls.extend(urls)
        print(f'   Найдено URL: {len(urls)}')
    
    unique_urls = list(set(all_urls))
    print(f'\n📊 Всего уникальных изображений: {len(unique_urls)}')
    
    if len(unique_urls) == 0:
        print('⚠️ Не найдено изображений для обработки!')
        return
    
    success_count = 0
    for i, (url, filename) in enumerate(unique_urls, 1):
        print(f'\n[{i}/{len(unique_urls)}] {filename}')
        result = download_image(url, filename)
        if result:
            success_count += 1
        time.sleep(0.1)
    
    print(f'\n✅ Готово! Загружено: {success_count}/{len(unique_urls)} изображений')
    print(f'📁 Папка: {IMAGE_CACHE_DIR}/')
    
    # Показываем содержимое папки
    print(f'\n📁 Содержимое {IMAGE_CACHE_DIR}/:')
    for f in os.listdir(IMAGE_CACHE_DIR):
        size_kb = os.path.getsize(os.path.join(IMAGE_CACHE_DIR, f)) // 1024
        print(f'   {f} ({size_kb} КБ)')

if __name__ == '__main__':
    main()
