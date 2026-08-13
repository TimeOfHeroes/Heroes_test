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

IMAGE_CACHE_DIR = 'images_cache'

# ПРАВИЛЬНЫЕ названия ваших CSV файлов
CSV_FILES = [
    'heroes.csv',                    # колонка: Картинка
    'item_images.csv',               # колонка: Картинка
    'Talent_description.csv'         # колонки: Картинка активная, Картинка неактивная
]

# Поля, в которых могут быть ссылки на картинки
IMAGE_FIELDS = [
    'Картинка',
    'Картинка активная',
    'Картинка неактивная',
    'image',
    'icon'
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
    
    cache_file = os.path.join(IMAGE_CACHE_DIR, filename)
    
    # Проверяем, есть ли уже оптимизированная версия
    if os.path.exists(cache_file):
        print(f'⏭️ Пропускаем (уже есть): {filename}')
        return cache_file
    
    try:
        print(f'⬇️ Скачиваем: {url[:80]}...')
        response = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        
        # Проверяем, SVG ли это
        content_type = response.headers.get('Content-Type', '').lower()
        is_svg = '.svg' in url.lower() or 'svg' in content_type
        
        if is_svg:
            # Для SVG просто сохраняем как есть
            with open(cache_file, 'wb') as f:
                f.write(response.content)
            size_kb = os.path.getsize(cache_file) // 1024
            print(f'✅ Сохранён SVG: {filename} ({size_kb} КБ)')
            return cache_file
        
        # Для растровых изображений используем Pillow
        try:
            img = Image.open(BytesIO(response.content))
        except Exception as e:
            # Если не удалось открыть как изображение — сохраняем как есть
            print(f'⚠️ Не удалось обработать как изображение, сохраняем как есть: {filename}')
            with open(cache_file, 'wb') as f:
                f.write(response.content)
            size_kb = os.path.getsize(cache_file) // 1024
            print(f'✅ Сохранён: {filename} ({size_kb} КБ)')
            return cache_file
        
        # Определяем формат и сохраняем
        if img.mode in ('RGBA', 'LA', 'P'):
            if img.mode == 'P':
                img = img.convert('RGBA')
            img.save(cache_file, 'PNG', optimize=True)
        else:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            if max_width and img.width > max_width:
                ratio = max_width / img.width
                new_size = (max_width, int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            img.save(cache_file, 'JPEG', quality=quality, optimize=True)
        
        size_kb = os.path.getsize(cache_file) // 1024
        print(f'✅ Оптимизировано: {filename} ({size_kb} КБ)')
        return cache_file
        
    except Exception as e:
        print(f'❌ Ошибка для {filename}: {e}')
        # Пробуем сохранить как есть
        try:
            print(f'🔄 Пробуем сохранить как есть...')
            with open(cache_file, 'wb') as f:
                f.write(response.content)
            size_kb = os.path.getsize(cache_file) // 1024
            print(f'✅ Сохранён как есть: {filename} ({size_kb} КБ)')
            return cache_file
        except:
            print(f'❌ Не удалось сохранить {filename}')
            return None

def process_csv_file(csv_path):
    """Обрабатывает CSV файл и извлекает URL изображений"""
    
    if not os.path.exists(csv_path):
        print(f'⚠️ Файл не найден: {csv_path}')
        return []
    
    urls = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Проверяем, какие колонки есть в файле
            print(f'   Колонки в файле: {list(reader.fieldnames)}')
            
            for row in reader:
                # Проверяем все колонки, которые могут содержать картинки
                for field in IMAGE_FIELDS:
                    if field in row and row[field]:
                        url = extract_url(row[field])
                        if url:
                            # Создаем имя файла из хеша
                            file_hash = get_image_hash(url)
                            # Определяем расширение
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
    print('🚀 Запуск оптимизации изображений...')
    print(f'📂 Рабочая папка: {os.getcwd()}')
    
    # Создаем папку для кеша
    os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)
    
    all_urls = []
    
    # Обрабатываем все CSV файлы
    for csv_file in CSV_FILES:
        print(f'\n📄 Обработка: {csv_file}')
        urls = process_csv_file(csv_file)
        all_urls.extend(urls)
        print(f'   Найдено URL: {len(urls)}')
    
    # Удаляем дубликаты
    unique_urls = list(set(all_urls))
    print(f'\n📊 Всего уникальных изображений: {len(unique_urls)}')
    
    if len(unique_urls) == 0:
        print('⚠️ Не найдено изображений для обработки!')
        print('   Проверьте, что CSV файлы содержат колонки с картинками')
        return
    
    # Скачиваем и оптимизируем
    success_count = 0
    for i, (url, filename) in enumerate(unique_urls, 1):
        print(f'\n[{i}/{len(unique_urls)}] {filename}')
        result = download_and_optimize_image(url, filename)
        if result:
            success_count += 1
        time.sleep(0.2)
    
    print(f'\n✅ Готово! Оптимизировано: {success_count}/{len(unique_urls)} изображений')
    print(f'📁 Папка: {IMAGE_CACHE_DIR}/')

if __name__ == '__main__':
    main()
