import math

# Константы, используемые в формуле
# Rз (Радиус Земли, км)
R_EARTH_KM = 6371.0
# Количество секунд в одном году
SEC_PER_YEAR = 31536000


def calculate_collision_financial_risk(
        N_objects: float,
        H_upper: float,
        H_lower: float,
        V_rel: float,
        A_effective: float,
        T_years: float,
        C_full: float,
        D_lost: float
) -> dict:
    """
    Рассчитывает ожидаемый финансовый риск (ФР) из-за столкновения
    космического аппарата с мусором за весь срок миссии.

    Формула:
    ФР = (1 - exp( -(N / V_shell) * V_отн * A * T_секунды )) * (Сполн + Дуп)

    Где V_shell - объем сферической оболочки.

    Аргументы:
        N_objects (float): Общее число отслеживаемых объектов (спутников и мусора)
                           в целевом орбитальном слое (N).
        H_upper (float): Верхняя высота орбитальной оболочки (Hв, в км).
        H_lower (float): Нижняя высота орбитальной оболочки (Hн, в км).
        V_rel (float): Средняя относительная скорость столкновения (Vотн, в км/с).
                       Типичное значение 10-15 км/с.
        A_effective (float): Эффективная площадь поперечного сечения спутника (A, в км²).
                             ВНИМАНИЕ: Должна быть в км²! (1 м² = 1e-6 км²).
        T_years (float): Срок службы миссии в годах (Tлет).
        C_full (float): Полная стоимость миссии (Сполн, в денежных единицах).
        D_lost (float): Упущенный доход в случае потери спутника (Дуп, в денежных единицах).

    Возвращает:
        float: Ожидаемый финансовый риск (ФР) в тех же денежных единицах.
    """

    # --- Часть 1: Расчет объема сферической оболочки (V_shell) ---
    # Блок (4/3 * π * ((Rз + Hв)³ - (Rз + Hн)³))

    # Радиусы внешней и внутренней границ объема в км
    R_upper = R_EARTH_KM + H_upper
    R_lower = R_EARTH_KM + H_lower

    # Расчет объема V_shell
    # (4/3) * π * (R_upper³ - R_lower³)
    V_shell = (4 / 3) * math.pi * (R_upper ** 3 - R_lower ** 3)

    # Проверка, чтобы избежать деления на ноль или отрицательного объема
    if V_shell <= 0:
        print("Ошибка: Объем V_shell меньше или равен нулю. Проверьте H_upper и H_lower.")
        return 0.0

    # --- Часть 2: Расчет ожидаемого числа столкновений (Expected_collisions) ---
    # Выражение в скобках экспоненты: (N / V_shell) * V_отн * A * T_секунды

    # Плотность объектов в объеме (N / V_shell) [объектов/км³]
    density = N_objects / V_shell

    # Срок миссии в секундах (Tлет * 31536000)
    T_seconds = T_years * SEC_PER_YEAR

    # Ожидаемое количество столкновений за всю миссию (lambda)
    # Это произведение плотности, относительной скорости, площади и времени
    expected_collisions = density * V_rel * (A_effective / 1000) * T_seconds

    # --- Часть 3: Расчет вероятности столкновения (P_collision) ---
    # Блок (1 - exp(-Expected_collisions))

    # Вероятность столкновения (P_collision)
    # Используем отрицательное значение в экспоненте
    P_collision = 1.0 - math.exp(-expected_collisions)

    # --- Часть 4: Расчет итогового финансового риска (ФР) ---
    # ФР = P_collision * (Сполн + Дуп)

    total_cost_at_risk = C_full + D_lost

    financial_risk = P_collision * total_cost_at_risk

    return {"financial_risk": round(financial_risk, 2), "collision_risk": P_collision}


def calculate_launch_collision_risk(
        N_objects: float,
        H_ascent: float,
        V_rel: float,
        A_rocket: float,
        T_seconds: float,
        C_total_loss: float
) -> dict:
    """
    Рассчитывает ожидаемый финансовый риск (ФР) из-за столкновения
    ракеты-носителя или спутника с мусором во время активного участка выведения.

    Формула:
    ФР = (1 - exp( - (N / V_corridor) * V_отн * A_ракета * T_секунды )) * C_total_loss

    Аргументы:
        N_objects (float): Общее число объектов (N) в объеме от Rз до Rз + H_ascent.
        H_ascent (float): Максимальная высота подъема (H_подъема, в км).
        V_rel (float): Средняя относительная скорость столкновения (V_отн, в км/с).
        A_rocket (float): Эффективная площадь поперечного сечения ракеты (A_ракета, в км²).
                          ВНИМАНИЕ: Должна быть в м²!.
        T_seconds (float): Общее время пролета до H_ascent в секундах (T_пролета_сек).
        C_total_loss (float): Сумма полной стоимости спутника и ракеты
                              (С_спутника + С_ракеты, в денежных единицах).

    Возвращает:
        float: Ожидаемый финансовый риск (ФР) при запуске.
    """

    # --- Часть 1: Расчет объема коридора выведения (V_corridor) ---
    # Блок (4/3 * π * ((Rз + H_подъема)³ - Rз³))

    # Радиус внешней границы объема в км (внутренняя граница - R_EARTH_KM)
    R_upper = R_EARTH_KM + H_ascent

    # Расчет объема V_corridor (от поверхности Земли до H_ascent)
    V_corridor = (4 / 3) * math.pi * (R_upper ** 3 - R_EARTH_KM ** 3)

    if V_corridor <= 0:
        print("Ошибка: Объем V_corridor меньше или равен нулю. Проверьте H_ascent.")
        return 0.0

    # --- Часть 2: Расчет ожидаемого числа столкновений (Expected_collisions) ---
    # Выражение в скобках экспоненты: (N / V_corridor) * V_отн * A_ракета * T_секунды

    # Плотность объектов в объеме (N / V_corridor) [объектов/км³]
    density = N_objects / V_corridor

    # Ожидаемое количество столкновений за время пролета (lambda)
    # Это произведение плотности, относительной скорости, площади и времени
    expected_collisions = density * V_rel * (A_rocket / 1000000) * T_seconds

    # --- Часть 3: Расчет вероятности столкновения (P_collision) ---
    # Блок (1 - exp(-Expected_collisions))

    P_collision = 1.0 - math.exp(-expected_collisions)

    # --- Часть 4: Расчет итогового финансового риска (ФР) ---
    # ФР = P_collision * C_total_loss

    financial_risk = P_collision * C_total_loss

    return {"financial_risk": round(financial_risk, 2), "collision_risk": P_collision}
