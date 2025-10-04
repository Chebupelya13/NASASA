import satellite_tracker
import json


def main():
    """
    Главная функция для демонстрации работы пакета satellite_tracker.
    """
    print("Запуск демонстрации работы трекера спутников...")

    # 1. Загрузка TLE-данных для всех активных спутников
    # Этот процесс может занять некоторое время
    tle_data = satellite_tracker.get_all_active_satellites()

    if not tle_data:
        print("Не удалось загрузить данные о спутниках. Завершение работы.")
        return

    print(f"Загружено TLE-данных для {len(tle_data)} спутников.")

    # 2. Определение параметров для анализа загруженности
    # Пример: Низкая околоземная орбита (НОО)
    min_alt = 300  # км
    max_alt = 2000  # км
    # Все наклонения
    min_inc = 0  # градусы
    max_inc = 180  # градусы

    print(f"\nРасчет загруженности для высот от {min_alt} км до {max_alt} км "
          f"и наклонений от {min_inc}° до {max_inc}°...")

    # 3. Расчет загруженности
    congestion = satellite_tracker.calculate_orbit_congestion_by_altitude(
        tle_data_dicts=tle_data,
        min_altitude_km=min_alt,
        max_altitude_km=max_alt,
        min_inclination=min_inc,
        max_inclination=max_inc
    )

    if not congestion:
        print("Не найдено спутников в заданных диапазонах.")
        return

    # 4. Вывод результатов
    # Сортируем ячейки по количеству спутников для наглядности
    sorted_congestion = sorted(
        congestion.items(),
        key=lambda item: item[1]['count'],
        reverse=True
    )

    print("\n--- Топ-10 самых загруженных орбитальных слоев ---")
    for i, (cell_key, data) in enumerate(sorted_congestion[:10]):
        mean_motion_bin, inclination_bin = cell_key
        print(
            f"{i + 1}. Слой (MM: {mean_motion_bin:.1f} об/сут, ~Накл: {inclination_bin}°):"
        )
        print(f"   - Количество спутников: {data['count']}")
        print(f"   - Среднее наклонение: {data['avg_inclination']:.2f}°")
        print(f"   - Среднее движение: {data['avg_mean_motion']:.4f} об/сут")

    # Можно также сохранить полные данные в файл для дальнейшего анализа
    # Преобразуем ключи-кортежи в строки для совместимости с JSON
    congestion_str_keys = {str(k): v for k, v in congestion.items()}
    with open("congestion_report.json", "w", encoding="utf-8") as f:
        json.dump(congestion_str_keys, f, indent=4, ensure_ascii=False)

    print("\nПолный отчет о загруженности сохранен в 'congestion_report.json'")
    print("Демонстрация завершена.")


if __name__ == "__main__":
    main()