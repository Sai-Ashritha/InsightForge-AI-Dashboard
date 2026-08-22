import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os


def generate_sales_data(num_records: int = 150) -> pd.DataFrame:
    """Generate realistic sales data."""
    start_date = datetime.now() - timedelta(days=365)
    dates = [start_date + timedelta(days=i) for i in range(num_records)]

    products = ["Widget A", "Widget B", "Widget C", "Gadget X", "Gadget Y"]
    categories = ["Electronics", "Hardware", "Accessories"]
    regions = ["North", "South", "East", "West", "Central"]

    data = {
        "date": dates,
        "product": np.random.choice(products, num_records),
        "category": np.random.choice(categories, num_records),
        "region": np.random.choice(regions, num_records),
        "quantity": np.random.randint(50, 500, num_records),
        "unit_price": np.random.uniform(100, 5000, num_records),
        "revenue": np.random.uniform(50000, 2500000, num_records),
    }

    df = pd.DataFrame(data)
    return df


def generate_production_data(num_records: int = 150) -> pd.DataFrame:
    """Generate realistic production data."""
    start_date = datetime.now() - timedelta(days=365)
    dates = [start_date + timedelta(days=i) for i in range(num_records)]

    products = ["Widget A", "Widget B", "Widget C", "Gadget X", "Gadget Y"]
    departments = ["Assembly", "Testing", "Packaging", "QC", "Maintenance"]

    data = {
        "date": dates,
        "product": np.random.choice(products, num_records),
        "department": np.random.choice(departments, num_records),
        "units_produced": np.random.randint(500, 2000, num_records),
        "defective_units": np.random.randint(5, 100, num_records),
        "machine_hours": np.random.uniform(8, 24, num_records),
        "downtime": np.random.uniform(0, 5, num_records),
    }

    df = pd.DataFrame(data)
    return df


def generate_inventory_data(num_records: int = 150) -> pd.DataFrame:
    """Generate realistic inventory data."""
    start_date = datetime.now() - timedelta(days=365)
    dates = [start_date + timedelta(days=i) for i in range(num_records)]

    products = ["Widget A", "Widget B", "Widget C", "Gadget X", "Gadget Y"]
    warehouses = ["Warehouse 1", "Warehouse 2", "Warehouse 3"]

    data = {
        "date": dates,
        "product": np.random.choice(products, num_records),
        "stock_available": np.random.randint(1000, 50000, num_records),
        "reorder_level": np.random.randint(500, 5000, num_records),
        "warehouse": np.random.choice(warehouses, num_records),
    }

    df = pd.DataFrame(data)
    return df


def generate_employees_data(num_records: int = 150) -> pd.DataFrame:
    """Generate realistic employee productivity data."""
    start_date = datetime.now() - timedelta(days=365)
    dates = [start_date + timedelta(days=i) for i in range(num_records)]

    departments = ["Assembly", "Testing", "Packaging", "QC", "Maintenance"]
    employee_ids = [f"EMP{i:05d}" for i in range(1, 51)]

    data = {
        "employee_id": np.random.choice(employee_ids, num_records),
        "department": np.random.choice(departments, num_records),
        "date": dates,
        "hours_worked": np.random.uniform(6, 10, num_records),
        "units_completed": np.random.randint(50, 500, num_records),
        "productivity": np.random.uniform(70, 105, num_records),
    }

    df = pd.DataFrame(data)
    return df


def generate_finance_data(num_records: int = 150) -> pd.DataFrame:
    """Generate realistic finance data."""
    start_date = datetime.now() - timedelta(days=365)
    dates = [start_date + timedelta(days=i) for i in range(num_records)]

    departments = ["Operations", "Sales", "R&D", "Administration", "Logistics"]

    data = {
        "date": dates,
        "department": np.random.choice(departments, num_records),
        "expense": np.random.uniform(50000, 500000, num_records),
        "profit": np.random.uniform(100000, 1000000, num_records),
        "revenue": np.random.uniform(200000, 2000000, num_records),
    }

    df = pd.DataFrame(data)
    return df


def export_to_csv(output_dir: str = "data/sample") -> None:
    """Generate and export all sample data to CSV files."""
    os.makedirs(output_dir, exist_ok=True)

    print("Generating sales data...")
    sales = generate_sales_data()
    sales_file = os.path.join(output_dir, "sales.csv")
    sales.to_csv(sales_file, index=False)
    print(f"✓ Exported {len(sales)} sales records to {sales_file}")

    print("Generating production data...")
    production = generate_production_data()
    production_file = os.path.join(output_dir, "production.csv")
    production.to_csv(production_file, index=False)
    print(f"✓ Exported {len(production)} production records to {production_file}")

    print("Generating inventory data...")
    inventory = generate_inventory_data()
    inventory_file = os.path.join(output_dir, "inventory.csv")
    inventory.to_csv(inventory_file, index=False)
    print(f"✓ Exported {len(inventory)} inventory records to {inventory_file}")

    print("Generating employee data...")
    employees = generate_employees_data()
    employees_file = os.path.join(output_dir, "employees.csv")
    employees.to_csv(employees_file, index=False)
    print(f"✓ Exported {len(employees)} employee records to {employees_file}")

    print("Generating finance data...")
    finance = generate_finance_data()
    finance_file = os.path.join(output_dir, "finance.csv")
    finance.to_csv(finance_file, index=False)
    print(f"✓ Exported {len(finance)} finance records to {finance_file}")


if __name__ == "__main__":
    export_to_csv()
