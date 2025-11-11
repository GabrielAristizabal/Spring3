CREATE TABLE IF NOT EXISTS orders (
  id SERIAL PRIMARY KEY,
  data JSONB NOT NULL,
  created_by TEXT,
  created_at TIMESTAMP,
  hash TEXT,
  signature TEXT
);

CREATE TABLE IF NOT EXISTS audit (
  id SERIAL PRIMARY KEY,
  order_id INTEGER REFERENCES orders(id),
  action TEXT,
  user_id TEXT,
  ts TIMESTAMP DEFAULT now(),
  old_data JSONB,
  new_data JSONB
);
