import math
from typing import List, Dict, Tuple, Any

from skyfield.api import EarthSatellite, load

# Загрузка таймскейла Skyfield
ts = load.timescale()

# Константы, необходимые для преобразования высоты в среднее движение.
# Они используются для фильтрации по высоте, так как TLE напрямую не содержит высоту.
MU_KM3_PER_S2 = 398600.4418  # Стандартный гравитационный параметр Земли (км^3/с^2)
EARTH_RADIUS_KM = 6378.137  # Средний экваториальный радиус Земли (км)


def _altitude_to_mean_motion(altitude_km: float) -> float:
    """
    Преобразует высоту орбиты (в предположении, что она круговая) в среднее движение.
    Это необходимо для фильтрации спутников по диапазону высот.
    """
    if altitude_km < 0:
        return 0.0

    orbital_radius_km = EARTH_RADIUS_KM + altitude_km

    try:
        # Формула периода обращения Кеплера
        period_seconds = 2 * math.pi * math.sqrt(orbital_radius_km**3 / MU_KM3_PER_S2)
    except ValueError:
        return 0.0

    if period_seconds == 0:
        return float("inf")

    # Преобразование периода в количество оборотов в сутки
    mean_motion_rev_per_day = 86400.0 / period_seconds
    return mean_motion_rev_per_day


def calculate_orbit_congestion_by_altitude(
    tle_data_dicts: List[Dict[str, Any]],
    min_altitude_km: float,  # Минимальная высота (км)
    max_altitude_km: float,  # Максимальная высота (км)
    min_inclination: float,  # Минимальное Наклонение (градусы)
    max_inclination: float,  # Максимальное Наклонение (градусы)
) -> Dict[Tuple[float, int], Dict[str, Any]]:
    """
    Рассчитывает загруженность орбитальных слоев, используя Skyfield для точного
    извлечения орбитальных параметров (наклонение, среднее движение) из TLE-данных.
    """
    # Шаг 1: Преобразование заданного диапазона высот в диапазон среднего движения
    # для последующей фильтрации.
    try:
        # MM_MAX соответствует МИН. высоте (более высокая скорость)
        max_mean_motion_filter = _altitude_to_mean_motion(min_altitude_km)
        # MM_MIN соответствует МАКС. высоте (более низкая скорость)
        min_mean_motion_filter = _altitude_to_mean_motion(max_altitude_km)
    except ValueError:
        print("Ошибка: Некорректный диапазон высот.")
        return {}

    print(
        f"Фильтр по среднему движению (об/сут): от {min_mean_motion_filter:.4f} до {max_mean_motion_filter:.4f}"
    )

    congestion_map: Dict[Tuple[float, int], Dict[str, Any]] = {}

    for sat_data in tle_data_dicts:
        name = sat_data.get("name", "UNKNOWN")
        line1 = sat_data.get("line1")
        line2 = sat_data.get("line2")

        if not line1 or not line2:
            continue

        try:
            # Шаг 2: Создание объекта EarthSatellite из TLE-строк
            satellite = EarthSatellite(line1, line2, name, ts)

            # Шаг 3: Извлечение и преобразование орбитальных параметров из модели спутника
            # Среднее движение (no_kozai) дано в радианах/минуту.
            # Преобразуем в обороты/сутки: (rad/min) * (1440 min/day) / (2*pi rad/rev)
            mean_motion = satellite.model.no_kozai * (1440.0 / (2 * math.pi))

            # Наклонение (inclo) дано в радианах. Преобразуем в градусы.
            inclination_deg = math.degrees(satellite.model.inclo)

            # Шаг 4: Фильтрация спутников по диапазонам среднего движения и наклонения
            if not (min_mean_motion_filter <= mean_motion <= max_mean_motion_filter):
                continue

            if not (min_inclination <= inclination_deg <= max_inclination):
                continue

            # Шаг 5: Кластеризация и агрегация данных о загруженности
            mean_motion_bin = round(mean_motion, 1)
            inclination_bin = int(round(inclination_deg))
            cell_key = (mean_motion_bin, inclination_bin)

            if cell_key not in congestion_map:
                congestion_map[cell_key] = {
                    "count": 0,
                    "avg_inclination": 0.0,
                    "avg_mean_motion": 0.0,
                }

            # Обновление данных в ячейке (счетчик и скользящее среднее)
            data = congestion_map[cell_key]
            current_count = data["count"]
            new_count = current_count + 1

            data["avg_inclination"] = (
                data["avg_inclination"] * current_count + inclination_deg
            ) / new_count
            data["avg_mean_motion"] = (
                data["avg_mean_motion"] * current_count + mean_motion
            ) / new_count
            data["count"] = new_count

        except Exception as e:
            # Пропускаем спутники, TLE которых не удалось обработать
            print(f"Ошибка при обработке спутника {name}: {e}")
            continue

    return congestion_map
