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
