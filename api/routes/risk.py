from datetime import datetime

from sanic import Blueprint
from sanic.response import json

from satellite_tracker import (
    get_all_active_satellites,
    calculate_orbit_congestion_by_altitude,
    calculate_satellite_position,
)
from utils.distance_calculation import quick_distance
from utils.risk_calculator import (
    calculate_collision_financial_risk,
    calculate_launch_collision_risk,
)

bp = Blueprint("risks", url_prefix="/")


@bp.get("/orbit_risk")
async def orbit_collision_risk(request):
    """
    Рассчет риска при нахождении на орбите.
    openapi:
    parameters:
      - name: height
        in: query
        description: Высота на орбите (км)
        required: true
        schema:
          type: integer
      - name: A_effective
        in: query
        description: Эффективная площадь поперечного сечения (м^2)
        schema:
          type: float
      - name: T_years
        in: query
        description:  Срок службы миссии в годах
        required: true
        schema:
          type: integer
      - name: C_full
        in: query
        description: Полная стоимость миссии
        required: true
        schema:
          type: integer
      - name: D_lost
        in: query
        description:  Упущенный доход в случае потери спутника
        required: true
        schema:
          type: integer
      - name: V_rel
        in: query
        description: Средняя относительная скорость столкновения (км/c)
        required: false
        schema:
          type: float
    """
    try:
        height = float(request.args["height"][0])
        a_effective = float(request.args["A_effective"][0])
        t_years = float(request.args["T_years"][0])
        c_full = float(request.args["C_full"][0])
        d_lost = float(request.args["D_lost"][0])
        v_rel = (
            float(request.args.get("V_rel")[0]) if request.args.get("V_rel") else 12.5
        )

        all_objects = get_all_active_satellites()
        # Теперь функция возвращает (congestion_map, filtered_satellites)
        congestion_map, _ = calculate_orbit_congestion_by_altitude(
            all_objects, height - 50, height + 50, 0, 180
        )

        # Считаем общее количество объектов из карты загруженности
        total_objects_in_layer = sum(data["count"] for data in congestion_map.values())

        orbit_risk = calculate_collision_financial_risk(
            total_objects_in_layer,
            height + 50,
            height - 50,
            v_rel,
            a_effective,
            t_years,
            c_full,
            d_lost,
        )

        return json(orbit_risk)

    except KeyError as e:
        return json({"message": f"Missing required parameter: {e.args[0]}"}, status=400)
    except (ValueError, TypeError):
        return json(
            {"message": "Invalid parameter type. Please provide valid numbers."},
            status=400,
        )


@bp.get("/takeoff_risk")
async def takeoff_collision_risk(request):
    """
    Рассчет риска при подъеме объекта.
    openapi:
    parameters:
        - name: lat
          in: query
          description: Широта мест азапуска
          required: false
          schema:
            type: float
            example: 49.99345
        - name: lon
          in: query
          description: долгота мест азапуска
          required: false
          schema:
            type: float
            example: 49.99345
        - name: date
          in: query
          description: Дата запуска миссии
          required: true
          schema:
            type: string
            example: "2025-10-04"

        - name: H_ascent
          in: query
          description: Высота (км), на которой заканчивается активный участок полета ракеты.
          required: true
          schema:
            type: number
            format: float
            example: 200.5

        - name: V_rel
          in: query
          description: Средняя относительная скорость столкновения (V_отн, в км/с).
          required: false
          schema:
            type: number
            format: float
            example: 7800.25

        - name: A_rocket
          in: query
          description: Эффективная площадь поперечного сечения ракеты (м²).
          required: true
          schema:
            type: number
            format: float
            example: 15.8

        - name: T_seconds
          in: query
          description: Продолжительность (секунды) определенного полета.
          required: true
          schema:
            type: number
            format: float
            example: 540.0

        - name: C_total_loss
          in: query
          description: Суммарные потери фиаско.
          required: true
          schema:
            type: number
            format: float
            example: 1800.75
    """
    try:
        date_str = request.args["date"][0]
        h_ascent = float(request.args["H_ascent"][0])
        a_rocket = float(request.args["A_rocket"][0])
        t_seconds = float(request.args["T_seconds"][0])
        c_total_loss = float(request.args["C_total_loss"][0])
        lat = float(request.args.get("lat")[0]) if request.args.get("lat") else None
        lon = float(request.args.get("lon")[0]) if request.args.get("lon") else None
        v_rel = (
            float(request.args.get("V_rel")[0]) if request.args.get("V_rel") else 12.5
        )

        # Теперь функция возвращает (congestion_map, filtered_satellites)
        # Нам нужен список отфильтрованных спутников для дальнейшей обработки
        _, filtered_satellites = calculate_orbit_congestion_by_altitude(
            get_all_active_satellites(), 0, h_ascent, 0, 180
        )

        N_objects = 0
        if lat is not None and lon is not None:
            launch_date = datetime.strptime(date_str, "%Y-%m-%d")
            for sat_data in filtered_satellites:  # Используем отфильтрованный список
                position = calculate_satellite_position(sat_data, launch_date)
                if quick_distance(position["lat"], position["lon"], lat, lon) < 10000:
                    N_objects += 1
        else:
            # Если lat/lon не предоставлены, считаем все объекты в диапазоне высот
            N_objects = len(filtered_satellites)

        orbit_risk = calculate_launch_collision_risk(
            N_objects,
            h_ascent,
            v_rel,
            a_rocket,
            t_seconds,
            c_total_loss,
        )

        return json(orbit_risk)

    except KeyError as e:
        return json({"message": f"Missing required parameter: {e.args[0]}"}, status=400)
    except (ValueError, TypeError):
        return json(
            {"message": "Invalid parameter type. Please provide valid numbers."},
            status=400,
        )
