from run_api import app


def test_health_check():
    """
    Тестирование эндпоинта /health.
    """
    request, response = app.test_client.get("/health")
    assert response.status == 200
    assert response.json == {"status": "OK"}


def test_orbit_risk_success():
    """
    Тестирование эндпоинта /orbit_risk с корректными параметрами.
    """
    params = {
        "height": "500",
        "A_effective": "10",
        "T_years": "5",
        "C_full": "1000000",
        "D_lost": "500000"
    }
    request, response = app.test_client.get('/orbit_risk', params=params)
    assert response.status == 200
    data = response.json
    assert "financial_risk" in data
    assert "collision_risk" in data


def test_orbit_risk_missing_params():
    """
    Тестирование эндпоинта /orbit_risk с отсутствующими параметрами.
    """
    params = {
        "height": "500",
    }
    request, response = app.test_client.get('/orbit_risk', params=params)
    assert response.status == 400
    data = response.json
    assert "message" in data
    assert "A_effective" in data["message"]


def test_takeoff_risk_success():
    """
    Тестирование эндпоинта /takeoff_risk с корректными параметрами.
    """
    params = {
        "lat": "49.99345",
        "lon": "49.99345",
        "date": "2025-10-04",
        "H_ascent": "200.5",
        "A_rocket": "15.8",
        "T_seconds": "540.0",
        "C_total_loss": "1800.75"
    }
    request, response = app.test_client.get('/takeoff_risk', params=params)
    assert response.status == 200
    data = response.json
    assert "financial_risk" in data
    assert "collision_risk" in data


def test_takeoff_risk_missing_params():
    """
    Тестирование эндпоинта /takeoff_risk с отсутствующими параметрами.
    """
    params = {
        "lat": "49.99345",
        "date": "2025-10-04",
    }
    request, response = app.test_client.get('/takeoff_risk', params=params)
    assert response.status == 400
    data = response.json
    assert "message" in data
    assert "H_ascent" in data["message"]