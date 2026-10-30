def test_list_invoices_returns_the_seed_invoice(client):
    response = client.get("/invoices")
    invoices = response.json()
    first_invoice = invoices[0]

    assert response.status_code == 200
    assert len(invoices) == 1
    assert first_invoice["customer_name"] == "Gupta Stores"
    assert first_invoice["amount_in_rupees"] == 10100.0


def test_overdue_invoices_includes_the_unpaid_late_invoice(client):
    response = client.get("/invoices/overdue")
    overdue_invoices = response.json()
    first_overdue_invoice = overdue_invoices[0]

    assert response.status_code == 200
    assert len(overdue_invoices) == 1
    assert first_overdue_invoice["status"] == "unpaid"


def test_get_one_invoice_returns_customer_email(client):
    response = client.get("/invoices/1")
    invoice = response.json()

    assert response.status_code == 200
    assert invoice["customer_email"] == "gupta@example.com"


def test_get_missing_invoice_returns_404(client):
    response = client.get("/invoices/99")

    assert response.status_code == 404


def test_marking_an_invoice_paid_removes_it_from_overdue(client):
    pay_response = client.post("/invoices/1/mark-paid")
    paid_invoice = pay_response.json()

    assert pay_response.status_code == 200
    assert paid_invoice["status"] == "paid"

    overdue_response = client.get("/invoices/overdue")
    overdue_invoices = overdue_response.json()

    assert len(overdue_invoices) == 0


def test_marking_the_same_invoice_paid_twice_is_refused(client):
    client.post("/invoices/1/mark-paid")

    second_response = client.post("/invoices/1/mark-paid")

    assert second_response.status_code == 409


def test_marking_a_missing_invoice_paid_returns_404(client):
    response = client.post("/invoices/99/mark-paid")

    assert response.status_code == 404