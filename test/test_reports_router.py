# test/test_reports_router.py

# ==========================================
# Get Low Stock Report
# ==========================================


def test_get_low_stock_report_should_return_report(client, make_ingredient):
    make_ingredient(quantity_on_hand=5, reorder_threshold=10)
    response = client.get("/reports/low-stock")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_low_stock_report_with_no_auth_should_return_401(unauthenticated_client):
    response = unauthenticated_client.get("/reports/low-stock")
    assert response.status_code == 401


def test_get_low_stock_report_with_no_manager_role_should_return_403(employee_client):
    response = employee_client.get("/reports/low-stock")
    assert response.status_code == 403


# ==========================================
# Get Usage Report
# ==========================================


def test_get_usage_report_should_return_report(client):
    response = client.get(
        "/reports/usage", params={"start_date": "2026-06-20", "end_date": "2026-06-26"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_usage_report_with_missing_query_parameters_should_return_422(client):
    response = client.get("/reports/usage")
    assert response.status_code == 422


def test_get_usage_report_with_invalid_date_format_should_return_422(client):
    response = client.get(
        "/reports/usage",
        params={"start_date": "twenty-twenty-six march thirty", "end_date": "2026-03"},
    )
    assert response.status_code == 422


def test_get_usage_report_with_no_auth_should_return_401(unauthenticated_client):
    response = unauthenticated_client.get(
        "/reports/usage", params={"start_date": "2026-07-14", "end_date": "2026-07-20"}
    )
    assert response.status_code == 401


def test_get_usage_report_with_no_manager_role_should_return_403(employee_client):
    response = employee_client.get(
        "/reports/usage", params={"start_date": "2026-02-22", "end_date": "2026-02-28"}
    )
    assert response.status_code == 403
