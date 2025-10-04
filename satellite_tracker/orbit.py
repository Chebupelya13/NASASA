from typing import List, Dict, Tuple, Any
from .utils import parse_and_get_value, altitude_to_mean_motion


def calculate_orbit_congestion_by_altitude(
        tle_data_dicts: List[Dict[str, Any]],
        min_altitude_km: float,  # Минимальная высота (км)
        max_altitude_km: float,  # Максимальная высота (км)
        min_inclination: float,  # Минимальное Наклонение (градусы)
        max_inclination: float  # Максимальное Наклонение (градусы)
) -> Dict[Tuple[float, int], Dict[str, Any]]:
    """
    Рассчитывает загруженность орбитальных слоев, фильтруя спутники по заданным
    диапазонам высот (км) и наклонения (°), используя только строковый парсинг.
    """

    # Шаг 1: Преобразование высот в диапазон Mean Motion
    try:
        # MM_MAX соответствует МИН. высоте
        max_mean_motion_filter = altitude_to_mean_motion(min_altitude_km)
        # MM_MIN соответствует МАКС. высоте
        min_mean_motion_filter = altitude_to_mean_motion(max_altitude_km)

    except ValueError:
        print("Ошибка: Некорректный диапазон высот.")
        return {}

    print(f"Фильтр MM преобразован: от {min_mean_motion_filter:.4f} до {max_mean_motion_filter:.4f} об/сут")

    congestion_map: Dict[Tuple[float, int], Dict[str, Any]] = {}

    for sat_data in tle_data_dicts:
        name = sat_data.get('name', 'UNKNOWN')
        line2 = sat_data.get('line2', '')

        if len(line2) < 69:
            continue

        try:
            # 2. Извлечение параметров с помощью строкового парсинга

            # Среднее Движение (Mean Motion)
            mean_motion = parse_and_get_value(line2, 53, 63)

            # Наклонение (Inclination)
            inclination_deg = parse_and_get_value(line2, 9, 16)

            if mean_motion == 0.0 or inclination_deg == 0.0:
                continue

            # 3. Фильтрация по заданным диапазонам

            # Фильтрация по Mean Motion (Высота)
            if not (min_mean_motion_filter <= mean_motion <= max_mean_motion_filter):
                continue

            # Фильтрация по Наклонению
            if not (min_inclination <= inclination_deg <= max_inclination):
                continue

            # 4. Кластеризация и Расчёт Загруженности

            # Кластер высоты (округляем Mean Motion до 0.1)
            mean_motion_bin = round(mean_motion, 1)

            # Кластер наклонения (округляем до целого градуса)
            inclination_bin = int(round(inclination_deg))

            cell_key = (mean_motion_bin, inclination_bin)

            if cell_key not in congestion_map:
                congestion_map[cell_key] = {
                    'count': 0,
                    'avg_inclination': 0.0,
                    'avg_mean_motion': 0.0,
                }

            # Обновление счетчика и скользящего среднего
            data = congestion_map[cell_key]
            current_count = data['count'] + 1

            data['avg_inclination'] = (data['avg_inclination'] * data['count'] + inclination_deg) / current_count
            data['avg_mean_motion'] = (data['avg_mean_motion'] * data['count'] + mean_motion) / current_count
            data['count'] = current_count

        except Exception as e:
            print(f"Неожиданная ошибка при обработке спутника {name}: {e}")
            continue

    return congestion_map