import requests
import time
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

CACHE_FILE = "/tmp/tle_cache.json"
CACHE_DURATION_HOURS = 4

def get_all_trackable_objects() -> List[Dict[str, Any]]:
    """
    Загружает и парсит TLE-данные для всех отслеживаемых объектов,
    используя файловый кэш для уменьшения количества запросов.
    """
    # Проверка кэша
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            try:
                cache_data = json.load(f)
                last_fetched_time = datetime.fromisoformat(cache_data["timestamp"])
                if datetime.utcnow() - last_fetched_time < timedelta(hours=CACHE_DURATION_HOURS):
                    print("CACHE HIT: Загрузка данных из кэша.")
                    return cache_data["data"]
            except (json.JSONDecodeError, KeyError, ValueError):
                print("CACHE ERROR: Ошибка чтения кэша. Будут загружены свежие данные.")

    # Если кэш недействителен или отсутствует, загружаем данные из сети
    print("CACHE MISS: Кэш недействителен или отсутствует. Загрузка свежих данных с CelesTrak.")

    base_url = "https://celestrak.org/NORAD/elements/gp.php"
    urls = {
        "active": f"{base_url}?GROUP=active&FORMAT=tle",
        "stations": f"{base_url}?GROUP=stations&FORMAT=tle",
        "rocket-bodies": f"{base_url}?GROUP=rocket-bodies&FORMAT=tle",
        "cosmos-1408-debris": f"{base_url}?GROUP=cosmos-1408-debris&FORMAT=tle",
        "iridium-33-debris": f"{base_url}?GROUP=iridium-33-debris&FORMAT=tle",
        "cosmos-2251-debris": f"{base_url}?GROUP=cosmos-2251-debris&FORMAT=tle",
        "fengyun-1c-debris": f"{base_url}?GROUP=fengyun-1c-debris&FORMAT=tle",
        "dmsp-f13-debris": f"{base_url}?GROUP=dmsp-f13-debris&FORMAT=tle",
        "breeze-m-debris": f"{base_url}?GROUP=breeze-m-debris&FORMAT=tle",
        "debris": f"{base_url}?GROUP=DEBRIS&FORMAT=tle",
        "decaying": f"{base_url}?SPECIAL=DECAYING&FORMAT=tle",
    }

    unique_objects: Dict[int, Dict[str, Any]] = {}

    for category, url in urls.items():
        print(f"Загрузка данных из категории '{category}' с {url}...")
        time.sleep(1)

        try:
            response = requests.get(url, timeout=90)
            response.raise_for_status()
            lines = response.text.strip().splitlines()
            print(f"Получено {len(lines) // 3} объектов из '{category}'.")

            for i in range(0, len(lines), 3):
                try:
                    name = lines[i].strip()
                    line1 = lines[i + 1].strip()
                    line2 = lines[i + 2].strip()
                    if len(line1) != 69 or len(line2) != 69:
                        continue
                    sat_num = int(line1[2:7])
                    unique_objects[sat_num] = {"name": name, "number": sat_num, "line1": line1, "line2": line2}
                except (IndexError, ValueError):
                    continue
        except requests.exceptions.RequestException as e:
            print(f"Произошла ошибка при запросе {url}: {e}")
            continue

    object_list = list(unique_objects.values())

    # Сохранение данных в кэш
    with open(CACHE_FILE, 'w') as f:
        cache_content = {
            "timestamp": datetime.utcnow().isoformat(),
            "data": object_list
        }
        json.dump(cache_content, f)

    print(f"Загрузка завершена. Всего уникальных объектов: {len(object_list)}. Кэш обновлен.")
    return object_list
