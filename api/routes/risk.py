import readline
from datetime import datetime

from sanic import Blueprint
from sanic.response import json

from satellite_tracker import get_all_active_satellites, calculate_orbit_congestion_by_altitude, \
    calculate_satellite_position
from utils.distance_calculation import quick_distance
from utils.risk_calculator import calculate_collision_financial_risk, calculate_launch_collision_risk

bp = Blueprint("risks", url_prefix="/")

@bp.get("/orbit_risk")
async def orbit_collision_risk(request):
    """
    Рассчет риска при нахождении на орбите.
    openapi:
    parameters:
      - name: height
        in: path
        description: Высота на орбите (км)
        required: true
        schema:
          type: integer
      - name: A_effective
        in: path
        description: Эффективная площадь поперечного сечения (м^2)
        schema:
          type: float
      - name: T_years
        in: path
        description:  Срок службы миссии в годах
        required: true
        schema:
          type: integer
      - name: C_full
        in: path
        description: Полная стоимость миссии
        required: true
        schema:
          type: integer
      - name: D_lost
        in: path
        description:  Упущенный доход в случае потери спутника
        required: true
        schema:
          type: integer
      - name: V_rel
        in: path
        description: Средняя относительная скорость столкновения (км/c)
        required: false
        schema:
          type: float
    """
    # try:
    all_objects = get_all_active_satellites()
    print("args", request.args)
    N_objects = calculate_orbit_congestion_by_altitude(all_objects, float(request.args["height"][0]) - 50, float(request.args["height"][0] )+ 50, 0, 180)

    orbit_risk = calculate_collision_financial_risk(
        len(N_objects),
        float(request.args["height"][0]) + 50,
        float(request.args["height"][0]) - 50,
        float(request.args.get("V_rel")[0]) if request.args.get("V_rel") else 12.5,
        float(request.args["A_effective"][0]),
        float(request.args["T_years"][0]),
        float(request.args["C_full"][0]),
        float(request.args["D_lost"][0])
    )

    return json(orbit_risk)

    # except KeyError:
    #     return json({"message": "Invalid request"})


@bp.get("/takeoff_risk")
async def takeoff_collision_risk(request):
    """
    Рассчет риска при подъеме объекта.
    openapi:
    parameters:
        - name: lat
          in: path
          description: Широта мест азапуска
          required: false
          schema:
            type: float
            example: 49.99345
        - name: lon
          in: path
          description: долгота мест азапуска
          required: false
          schema:
            type: float
            example: 49.99345
        - name: date
          in: path
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
        print(request.args)
        all_objects = calculate_orbit_congestion_by_altitude(get_all_active_satellites(), 0, float(request.args["H_ascent"][0]), 0, 180)
        N_objects = 0
        for sat_data in all_objects:
            position = calculate_satellite_position(sat_data, datetime.strptime(request.args["date"][0], "%Y-%m-%d"))
            if quick_distance(
                position["lat"],
                position["lon"],
                float(request.args["lat"][0]),
                float(request.args["lon"][0]),
            ):
                print('y')
                N_objects += 1


        orbit_risk = calculate_launch_collision_risk(
            N_objects,
            request.args["H_ascent"],
            request.args.get("V_rel") if request.args.get("V_rel") else 12.5,
            request.args["A_rocket"],
            request.args["T_seconds"],
            request.args["C_total_lose"],
        )

        return json(orbit_risk)

    except KeyError:
        return json({"message": "Invalid request"})