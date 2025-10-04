import requests
from typing import List, Dict, Any


def get_all_active_satellites() -> List[Dict[str, Any]]:
    """
    Загружает и парсит TLE-данные для всех активных спутников с CelesTrak.
    """
    # URL для получения TLE всех активных спутников
    url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"

    satellites: List[Dict[str, Any]] = []

    print(f"Загрузка данных с {url}...")
    try:
        response = requests.get(url)
        # Проверка на ошибки HTTP
        response.raise_for_status()

        # Разделяем весь текст на строки
        lines = response.text.strip().splitlines()
        print("Данные успешно загружены. Начинаю парсинг...")

        # TLE данные идут блоками по 3 строки: Имя, Строка 1, Строка 2
        # Мы итерируемся с шагом 3
        for i in range(0, len(lines), 3):
            name = lines[i].strip()
            line1 = lines[i + 1].strip()
            line2 = lines[i + 2].strip()

            # Извлекаем номер спутника из первой строки TLE
            sat_num = int(line1[2:7])

            satellites.append({
                "name": name,
                "number": sat_num,
                "line1": line1,
                "line2": line2
            })

        return satellites

    except requests.exceptions.RequestException as e:
        print(f"Произошла ошибка при запросе: {e}")
        return []
