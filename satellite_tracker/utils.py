import math

# Константы для преобразования высоты (h) в Mean Motion (об/сутки)
# Источник: Kepler's Third Law
MU_KM3_PER_S2 = 398600.4418  # Стандартный гравитационный параметр Земли (км^3/с^2)
EARTH_RADIUS_KM = 6378.137  # Средний экваториальный радиус Земли (км)


def parse_and_get_value(line: str, start: int, end: int) -> float:
    """Извлекает числовое значение из TLE-строки по колонкам (1-индексация) и преобразует в float."""
    # TLE-колонки считаются с 1. В Python - с 0.
    raw_value = line[start - 1: end].strip()
    if not raw_value:
        return 0.0
    try:
        # TLE format can use an implicit decimal point
        if raw_value.startswith('-') and raw_value[1] == '.':
            return float("-0" + raw_value[1:])
        elif raw_value.startswith('+') and raw_value[1] == '.':
            return float("0" + raw_value[1:])
        elif raw_value.startswith('.'):
            return float("0" + raw_value)

        # Handle scientific notation like "12345-6" -> 0.12345e-6
        if '-' in raw_value[1:] or '+' in raw_value[1:]:
            parts = raw_value.replace('+', 'e+').replace('-', 'e-').split('e')
            if len(parts) == 3 and parts[0] == '': # scientific notation starting with a sign
                base = parts[1]
                exponent = parts[2]
                return float(f"-0.{base}e-{exponent}")
            elif len(parts) == 2:
                base = parts[0]
                exponent = parts[1]
                if len(base) > 1: # e.g. 12345-6
                    return float(f"0.{base[:-1]}e{base[-1]}{exponent}")
                else: # e.g. 5-4
                     return float(f"0.{base}e-{exponent}")


        return float(raw_value)
    except (ValueError, IndexError):
        return 0.0


def altitude_to_mean_motion(altitude_km: float) -> float:
    """Преобразует высоту в километрах в Среднее Движение (Mean Motion, об/сутки)."""
    if altitude_km <= 0:
        # For LEO, negative altitude is non-physical. For HEO, it might be part of the orbit.
        # However, for mean motion calculation based on a circular orbit assumption, it's invalid.
        return 0.0  # Return 0 as it's an invalid input for this specific calculation.

    # Полный радиус орбиты (R = R_E + h)
    orbital_radius_km = EARTH_RADIUS_KM + altitude_km

    # Расчет периода в секундах (T = 2 * pi * sqrt(R^3 / mu))
    try:
        period_seconds = 2 * math.pi * math.sqrt(
            orbital_radius_km ** 3 / MU_KM3_PER_S2
        )
    except ValueError: # math domain error if orbital_radius_km is negative
        return 0.0

    if period_seconds == 0:
        return float('inf')

    # Расчет Mean Motion (N = 1 / (T / 86400))
    # N = (секунд в сутках) / период в секундах
    mean_motion_rev_per_day = 86400 / period_seconds

    return mean_motion_rev_per_day