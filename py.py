import pandas as pd
import pymysql

print("Starting script...")

try:
    # 1. Učitaj CSV
    df = pd.read_csv('german_verbs.csv', sep=';')
    print(f"CSV loaded: {len(df)} rows, columns: {list(df.columns)}")

    # 2. Zamijeni NaN sa None (MySQL koristi NULL)
    df = df.where(pd.notnull(df), "")

    # 3. Poveži se na MySQL
    connection = pymysql.connect(
        host='mirikoni.mysql.pythonanywhere-services.com',
        user='mirikoni',
        password='necemociovenoci',
        database='mirikoni$GermanFlaskApp',
        charset='utf8mb4'
    )
    cursor = connection.cursor()

    # 4. Obrisi tablicu ako postoji
    cursor.execute("DROP TABLE IF EXISTS irregularverbs;")

    # 5. Kreiraj CREATE TABLE SQL automatski prema kolonama CSV-a
    columns_sql = ', '.join([f"`{col}` VARCHAR(255)" for col in df.columns])
    create_table_sql = f"CREATE TABLE irregularverbs ({columns_sql}) CHARACTER SET utf8mb4;"
    cursor.execute(create_table_sql)
    print("Table created successfully.")

    # 6. Ubaci podatke
    cols = ', '.join([f"`{col}`" for col in df.columns])
    placeholders = ', '.join(['%s'] * len(df.columns))
    insert_sql = f"INSERT INTO irregularverbs ({cols}) VALUES ({placeholders})"

    data = [tuple(x) for x in df.to_numpy()]
    cursor.executemany(insert_sql, data)
    connection.commit()
    print(f"{len(data)} rows inserted successfully.")

    cursor.close()
    connection.close()

except Exception as e:
    print("An error occurred:", e)
