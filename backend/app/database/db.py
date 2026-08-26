import os

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

TABLE_FIELD_MAP = {
    "sales": [
        "date",
        "product",
        "category",
        "region",
        "quantity",
        "unit_price",
        "revenue",
    ],
    "production": [
        "date",
        "product",
        "department",
        "units_produced",
        "defective_units",
        "machine_hours",
        "downtime",
    ],
    "inventory": [
        "date",
        "product",
        "stock_available",
        "reorder_level",
        "warehouse",
    ],
    "employees": [
        "employee_id",
        "department",
        "date",
        "hours_worked",
        "units_completed",
        "productivity",
    ],
    "finance": [
        "date",
        "department",
        "expense",
        "profit",
        "revenue",
    ],
}

COLUMN_ALIASES = {
    "sales": {
        "date": ["date", "sales_date", "order_date"],
        "product": ["product", "item", "product_name"],
        "category": ["category", "segment"],
        "region": ["region", "territory", "market"],
        "quantity": ["quantity", "units_sold", "qty"],
        "unit_price": ["unit_price", "price", "unit_cost"],
        "revenue": ["revenue", "sales_value", "total_revenue"],
    },
    "production": {
        "date": ["date", "production_date"],
        "product": ["product", "item", "product_name"],
        "department": ["department", "work_center"],
        "units_produced": ["units_produced", "output", "produced_units"],
        "defective_units": ["defective_units", "defects", "rejected_units"],
        "machine_hours": ["machine_hours", "runtime_hours"],
        "downtime": ["downtime", "downtime_hours"],
    },
    "inventory": {
        "date": ["date", "inventory_date"],
        "product": ["product", "item", "product_name"],
        "stock_available": ["stock_available", "inventory_on_hand", "stock"],
        "reorder_level": ["reorder_level", "min_stock"],
        "warehouse": ["warehouse", "location", "storage_site"],
    },
    "employees": {
        "employee_id": ["employee_id", "emp_id", "employee"],
        "department": ["department", "team"],
        "date": ["date", "work_date"],
        "hours_worked": ["hours_worked", "hours"],
        "units_completed": ["units_completed", "output_units"],
        "productivity": ["productivity", "efficiency"],
    },
    "finance": {
        "date": ["date", "finance_date"],
        "department": ["department", "cost_center"],
        "expense": ["expense", "cost", "total_expense"],
        "profit": ["profit", "gross_profit"],
        "revenue": ["revenue", "sales_revenue"],
    },
}


def _normalize_column_name(name):
    return str(name).strip().lower().replace(" ", "_").replace("-", "_").replace("/", "_")


def infer_table_for_dataframe(df: pd.DataFrame):
    if df is None or df.empty:
        return "sales"

    columns = set(_normalize_column_name(col) for col in df.columns)
    best_table = "sales"
    best_score = -1

    for table_name, expected_columns in TABLE_FIELD_MAP.items():
        all_table_cols = set(expected_columns)
        for aliases in COLUMN_ALIASES.get(table_name, {}).values():
            all_table_cols.update(aliases)
        
        score = len(columns.intersection(all_table_cols))
        if score > best_score:
            best_score = score
            best_table = table_name

    return best_table


def normalize_dataframe_for_table(df: pd.DataFrame, table_name: str):
    if df is None or df.empty:
        return pd.DataFrame(columns=TABLE_FIELD_MAP.get(table_name, []))

    normalized = df.copy()
    normalized.columns = [_normalize_column_name(col) for col in normalized.columns]

    expected_columns = TABLE_FIELD_MAP.get(table_name, [])
    alias_map = COLUMN_ALIASES.get(table_name, {})

    renamed_columns = {}
    for target_col, aliases in alias_map.items():
        for alias in [target_col, *aliases]:
            if alias in normalized.columns:
                renamed_columns[target_col] = normalized[alias]
                break

    for target_col in expected_columns:
        if target_col in normalized.columns:
            continue
        if target_col in renamed_columns:
            normalized[target_col] = renamed_columns[target_col]

    for missing_col in expected_columns:
        if missing_col not in normalized.columns:
            normalized[missing_col] = None

    normalized = normalized[expected_columns]

    for col in ["date"]:
        if col in normalized.columns:
            normalized[col] = pd.to_datetime(normalized[col], errors="coerce")

    numeric_columns = {
        "quantity",
        "unit_price",
        "revenue",
        "units_produced",
        "defective_units",
        "machine_hours",
        "downtime",
        "stock_available",
        "reorder_level",
        "hours_worked",
        "units_completed",
        "productivity",
        "expense",
        "profit",
    }

    for col in numeric_columns:
        if col in normalized.columns:
            normalized[col] = pd.to_numeric(normalized[col], errors="coerce")

    return normalized


def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        db_url = db_url.replace("postgresql+psycopg://", "postgresql://", 1)
        connection_args = {"dsn": db_url}
    else:
        connection_args = {
            "dbname": os.getenv("POSTGRES_DB", "insightforge"),
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", "Project@123"),
            "host": os.getenv("POSTGRES_HOST", "127.0.0.1"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
        }

    try:
        return psycopg2.connect(**connection_args)
    except Exception as exc:
        raise RuntimeError(f"Database connection failed: {exc}") from exc


def create_tables():
    sql = """
    CREATE TABLE IF NOT EXISTS sales (
        id SERIAL PRIMARY KEY,
        date DATE,
        product VARCHAR(100),
        category VARCHAR(100),
        region VARCHAR(100),
        quantity INTEGER,
        unit_price FLOAT,
        revenue FLOAT
    );

    CREATE TABLE IF NOT EXISTS production (
        id SERIAL PRIMARY KEY,
        date DATE,
        product VARCHAR(100),
        department VARCHAR(100),
        units_produced INTEGER,
        defective_units INTEGER,
        machine_hours FLOAT,
        downtime FLOAT
    );

    CREATE TABLE IF NOT EXISTS inventory (
        id SERIAL PRIMARY KEY,
        date DATE,
        product VARCHAR(100),
        stock_available INTEGER,
        reorder_level INTEGER,
        warehouse VARCHAR(100)
    );

    CREATE TABLE IF NOT EXISTS employees (
        id SERIAL PRIMARY KEY,
        employee_id VARCHAR(100),
        department VARCHAR(100),
        date DATE,
        hours_worked FLOAT,
        units_completed INTEGER,
        productivity FLOAT
    );

    CREATE TABLE IF NOT EXISTS finance (
        id SERIAL PRIMARY KEY,
        date DATE,
        department VARCHAR(100),
        expense FLOAT,
        profit FLOAT,
        revenue FLOAT
    );

    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        role VARCHAR(20) NOT NULL DEFAULT 'viewer',
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT users_role_check CHECK (role IN ('admin', 'analyst', 'viewer'))
    );
    """

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        return {"status": "tables_created"}
    except Exception as exc:
        raise RuntimeError(f"Table creation failed: {exc}") from exc
    finally:
        conn.close()


def create_user(email: str, hashed_password: str, role: str = "analyst"):
    from app.database.orm import orm_create_user

    if role not in {"admin", "analyst", "viewer"}:
        raise ValueError("Invalid user role")
    user = orm_create_user(email=email, hashed_password=hashed_password, role=role)
    return {"id": user.id, "email": user.email, "role": user.role, "is_active": user.is_active}


def get_user_by_email(email: str):
    from app.database.orm import orm_get_user_by_email

    user = orm_get_user_by_email(email)
    if not user:
        return None
    return {
        "id": user.id,
        "email": user.email,
        "hashed_password": user.hashed_password,
        "role": user.role,
        "is_active": user.is_active,
    }


def clear_table(table_name: str):
    allowed_tables = set(TABLE_FIELD_MAP) | {"users"}
    if table_name not in allowed_tables:
        raise ValueError(f"Unsupported table: {table_name}")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"DELETE FROM {table_name}")
        conn.commit()
    finally:
        conn.close()


def insert_dataframe_to_table(df: pd.DataFrame, table_name: str):
    if df is None or df.empty:
        return {"table": table_name, "inserted_rows": 0}

    normalized_df = normalize_dataframe_for_table(df, table_name)
    columns = list(normalized_df.columns)
    placeholders = ", ".join(["%s"] * len(columns))
    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            for _, row in normalized_df.iterrows():
                values = []
                for value in row.tolist():
                    if pd.isna(value):
                        values.append(None)
                    elif isinstance(value, pd.Timestamp):
                        values.append(value.to_pydatetime())
                    else:
                        values.append(value)
                cur.execute(insert_sql, tuple(values))
        conn.commit()
        return {"table": table_name, "inserted_rows": len(normalized_df)}
    except Exception as exc:
        raise RuntimeError(f"Insert into table failed: {exc}") from exc
    finally:
        conn.close()


def save_uploaded_dataframe(df: pd.DataFrame, clear_existing: bool = True):
    normalized_columns = {_normalize_column_name(column) for column in df.columns}
    combined_columns = {"production", "inventory", "employees", "efficiency", "defect_rate"}

    if normalized_columns.intersection(combined_columns):
        source = df.copy()
        source.columns = [_normalize_column_name(column) for column in source.columns]
        inserted_tables = []
        inserted_rows = 0
        target_tables = ["sales", "production", "inventory", "employees"]

        if clear_existing:
            for table_name in target_tables:
                clear_table(table_name)

        sales_data = source[[column for column in ["date", "product", "region", "quantity", "revenue"] if column in source.columns]].copy()
        if not sales_data.empty:
            result = insert_dataframe_to_table(sales_data, "sales")
            inserted_tables.append("sales")
            inserted_rows += result["inserted_rows"]

        if "production" in source.columns:
            production_data = source[[column for column in ["date", "product", "production", "defect_rate"] if column in source.columns]].copy()
            production_data = production_data.rename(columns={"production": "units_produced"})
            if "defect_rate" in production_data.columns and "units_produced" in production_data.columns:
                production_data["defective_units"] = (
                    pd.to_numeric(production_data["units_produced"], errors="coerce")
                    * pd.to_numeric(production_data["defect_rate"], errors="coerce")
                    / 100
                ).round().fillna(0)
            result = insert_dataframe_to_table(production_data, "production")
            inserted_tables.append("production")
            inserted_rows += result["inserted_rows"]

        if "inventory" in source.columns:
            inventory_data = source[[column for column in ["date", "product", "inventory"] if column in source.columns]].copy()
            inventory_data = inventory_data.rename(columns={"inventory": "stock_available"})
            result = insert_dataframe_to_table(inventory_data, "inventory")
            inserted_tables.append("inventory")
            inserted_rows += result["inserted_rows"]

        if "employees" in source.columns:
            employee_data = source[[column for column in ["date", "employees", "efficiency"] if column in source.columns]].copy()
            employee_data["employee_id"] = [f"upload-{index + 1}" for index in range(len(employee_data))]
            employee_data = employee_data.rename(columns={"efficiency": "productivity"})
            result = insert_dataframe_to_table(employee_data, "employees")
            inserted_tables.append("employees")
            inserted_rows += result["inserted_rows"]

        return {
            "table": ", ".join(inserted_tables),
            "inserted_rows": inserted_rows,
            "tables": inserted_tables,
        }

    table_name = infer_table_for_dataframe(df)
    if clear_existing:
        if table_name == "sales":
            clear_table("production")
            clear_table("inventory")
            clear_table("employees")
        clear_table(table_name)
    else:
        clear_table(table_name)
    return insert_dataframe_to_table(df, table_name)


def fetch_table(table_name: str, limit: int | None = None):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = f"SELECT * FROM {table_name}"
            if limit is not None:
                query += " LIMIT %s"
                cur.execute(query, (limit,))
            else:
                cur.execute(query)
            rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
