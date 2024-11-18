import asyncio
import textwrap
from typing import AsyncGenerator, Generator
import asyncpg
from asyncpg import Record
from random import randint, sample


from utils import async_timed

CREATE_BRAND_TABLE = """
CREATE TABLE IF NOT EXISTS brand(
brand_id SERIAL PRIMARY KEY,
brand_name TEXT NOT NULL
);
"""
CREATE_PRODUCT_TABLE = """
CREATE TABLE IF NOT EXISTS product(
product_id SERIAL PRIMARY KEY,
product_name TEXT NOT NULL,
brand_id INT NOT NULL,
FOREIGN KEY (brand_id) REFERENCES brand(brand_id)
);"""

CREATE_PRODUCT_COLOR_TABLE = """
CREATE TABLE IF NOT EXISTS product_color(
product_color_id SERIAL PRIMARY KEY,
product_color_name TEXT NOT NULL
);"""

CREATE_PRODUCT_SIZE_TABLE = """
CREATE TABLE IF NOT EXISTS product_size(
product_size_id SERIAL PRIMARY KEY,
product_size_name TEXT NOT NULL
);"""

CREATE_SKU_TABLE = """
CREATE TABLE IF NOT EXISTS sku(
sku_id SERIAL PRIMARY KEY,
product_id INT NOT NULL,
product_size_id INT NOT NULL,
product_color_id INT NOT NULL,
FOREIGN KEY (product_id) REFERENCES product(product_id),
FOREIGN KEY (product_size_id) REFERENCES product_size(product_size_id),
FOREIGN KEY (product_color_id) REFERENCES product_color(product_color_id)
);"""
COLOR_INSERT = """
INSERT INTO product_color VALUES(1, 'Blue');
INSERT INTO product_color VALUES(2, 'Black');
"""
SIZE_INSERT = """
INSERT INTO product_size VALUES(1, 'Small');
INSERT INTO product_size VALUES(2, 'Medium');
INSERT INTO product_size VALUES(3, 'Large');
"""


def load_common_words() -> list[str]:
    with open("common_words.txt") as common_words:
        return common_words.readlines()


def generate_brand_names(words: list[str]) -> list[tuple[str]]:
    return [(words[index],) for index in sample(range(100), 100)]


async def insert_brands(common_words: list[str], connection) -> int:
    brands = generate_brand_names(common_words)
    insert_brands = "INSERT INTO brand VALUES(DEFAULT, $1)"
    return await connection.executemany(insert_brands, brands)


def gen_products(
    common_words: list[str],
    brand_id_start: int,
    brand_id_end: int,
    products_to_create: int,
) -> list[tuple[str, int]]:
    products = []
    for _ in range(products_to_create):
        name = " ".join(common_words[index] for index in sample(range(1000), 10))
        brand_id = randint(brand_id_start, brand_id_end)
        products.append((name, brand_id))
    return products


def gen_skus(
    product_id_start: int,
    product_id_end: int,
    skus_to_create: int,
) -> list[tuple[int, int, int]]:
    skus = []
    for _ in range(skus_to_create):
        product_id = randint(product_id_start, product_id_end)
        size_id = randint(1, 3)
        color_id = randint(1, 2)
        skus.append((product_id, size_id, color_id))
    return skus


async def main():
    conn = await asyncpg.connect(
        host="127.0.0.1",
        port=5432,
        user="postgres",
        database="products",
        password="password",
    )
    async with conn.transaction():
        stmts = [
            CREATE_BRAND_TABLE,
            CREATE_PRODUCT_TABLE,
            CREATE_PRODUCT_COLOR_TABLE,
            CREATE_PRODUCT_SIZE_TABLE,
            CREATE_SKU_TABLE,
            SIZE_INSERT,
            COLOR_INSERT,
        ]
        print("Creating the product database...")
        for stmt in stmts:
            status = await conn.execute(stmt)
            print(status)
        print("Finished creating the product database!")

        common_words = load_common_words()
        await insert_brands(common_words, conn)

        product_tuples = gen_products(
            common_words, brand_id_start=1, brand_id_end=100, products_to_create=1_000
        )
        await conn.executemany(
            "INSERT INTO product VALUES(DEFAULT, $1, $2)", product_tuples
        )

        sku_tuples = gen_skus(
            product_id_start=1, product_id_end=1000, skus_to_create=100_000
        )
        await conn.executemany(
            "INSERT INTO sku VALUES(DEFAULT, $1, $2, $3)", sku_tuples
        )


if __name__ == "__main__":
    asyncio.run(main())
