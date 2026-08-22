def calculate_kpis(data):
    if not data:
        return {
            "revenue": 0,
            "production": 0,
            "inventory": 0,
            "efficiency": 0,
            "defect_rate": 0,
            "employees": 0,
            "orders": 0,
        }

    revenue = sum(item.get("revenue", 0) for item in data)
    production = sum(item.get("production", 0) for item in data)
    inventory = sum(item.get("inventory", 0) for item in data)
    efficiency = sum(item.get("efficiency", 0) for item in data) / len(data)
    defect_rate = sum(item.get("defect_rate", 0) for item in data) / len(data)
    employees = sum(item.get("employees", 0) for item in data)
    orders = sum(item.get("orders", 0) for item in data)

    return {
        "revenue": round(revenue, 2),
        "production": round(production, 2),
        "inventory": round(inventory, 2),
        "efficiency": round(efficiency, 2),
        "defect_rate": round(defect_rate, 2),
        "employees": round(employees, 2),
        "orders": round(orders, 2),
    }
