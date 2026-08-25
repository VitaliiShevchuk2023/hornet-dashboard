"""
Завантаження семплу NABU hornet-спостережень у Neo4j Aura.
Джерело: Data_NABU_Hornet_Campaign_2025.xlsx (сирий naturgucker-експорт)

Модель графа:
  (:Observation {id, date, location, observation_type, photo_verified})
     -[:OF_SPECIES]->(:Species {name})
     -[:LOCATED_IN]->(:Bundesland {name})
     -[:HAS_HABITAT_HINT]->(:LocalityKeyword {type})

Запуск: python load_observations.py [--sample-size 200] [--full]
"""
import os
import sys
import argparse
import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD")

EXCEL_PATH = os.getenv("NABU_EXCEL_PATH", "Data_NABU_Hornet_Campaign_2025.xlsx")

SPECIES_MAP = {
    "crabro": "Vespa crabro",
    "velutina": "Vespa velutina",
}

# Habitat keyword proxy — той самий підхід, що в pages/4_Habitat.py,
# але застосований до поля Gebietsname (аналог GBIF "locality")
HABITAT_KEYWORDS = {
    "forest":     ["wald", "forst", "forest", "gehölz", "baum"],
    "field":      ["feld", "flur", "wiese", "meadow", "field"],
    "garden":     ["garten", "garden", "park", "grün"],
    "settlement": ["stadt", "dorf", "ortschaft", "siedlung", "urban"],
    "water":      ["bach", "fluss", "see", "teich", "wasser", "river"],
    "wetland":    ["moor", "sumpf", "feucht", "wetland"],
}

NEST_KEYWORDS = ["nest"]  # покриває "am/im Nest", "Nest(er)", "Nest(er), leer"


def classify_habitat(gebietsname: str) -> str:
    if not isinstance(gebietsname, str):
        return "unknown"
    loc = gebietsname.lower()
    for habitat, keywords in HABITAT_KEYWORDS.items():
        if any(kw in loc for kw in keywords):
            return habitat
    return "other"


def classify_observation_type(beobachtung: str) -> str:
    if not isinstance(beobachtung, str):
        return "sighting"
    b = beobachtung.lower()
    if any(kw in b for kw in NEST_KEYWORDS):
        return "nest"
    return "sighting"


def load_and_prepare(excel_path: str, sample_size):
    print(f"📂 Читаю {excel_path} ...")
    df = pd.read_excel(excel_path)

    # Фільтр тільки на два види шершнів
    df = df[df["Art"].isin(SPECIES_MAP.keys())].copy()
    print(f"   Знайдено {len(df)} записів hornet (crabro + velutina)")

    # Прибираємо записи без координат/дати (обов'язкові поля)
    df = df.dropna(subset=["Koordinate E", "Koordinate N", "Datum", "DatensatzID"])

    if sample_size:
        df = df.sample(n=min(sample_size, len(df)), random_state=42)
        print(f"   Семпл: {len(df)} записів (random_state=42, відтворюваний)")

    # Мапінг полів
    df["species_name"] = df["Art"].map(SPECIES_MAP)
    df["bundesland"] = df["Provinz"].fillna("Unknown")
    df["habitat_type"] = df["Gebietsname"].apply(classify_habitat)
    df["observation_type"] = df["Beobachtung"].apply(classify_observation_type)
    df["photo_verified"] = df["Belegbildlink"].notna()
    df["date_str"] = pd.to_datetime(df["Datum"]).dt.strftime("%Y-%m-%d")

    return df


def load_to_neo4j(driver, df, batch_size=200):
    rows = [{
        "id": str(r["DatensatzID"]),
        "species": r["species_name"],
        "lat": float(r["Koordinate N"]),   # Koordinate N = latitude
        "lon": float(r["Koordinate E"]),   # Koordinate E = longitude
        "date": r["date_str"],
        "bundesland": r["bundesland"],
        "habitat_type": r["habitat_type"],
        "observation_type": r["observation_type"],
        "photo_verified": bool(r["photo_verified"]),
    } for _, r in df.iterrows()]

    def _load_batch(tx, batch):
        tx.run("""
            UNWIND $rows AS row
            MERGE (o:Observation {id: row.id})
            SET o.date = date(row.date),
                o.location = point({latitude: row.lat, longitude: row.lon}),
                o.observation_type = row.observation_type,
                o.photo_verified = row.photo_verified

            MERGE (s:Species {name: row.species})
            MERGE (o)-[:OF_SPECIES]->(s)

            MERGE (b:Bundesland {name: row.bundesland})
            MERGE (o)-[:LOCATED_IN]->(b)

            MERGE (h:LocalityKeyword {type: row.habitat_type})
            MERGE (o)-[:HAS_HABITAT_HINT]->(h)
        """, rows=batch)

    total = len(rows)
    with driver.session() as session:
        for i in range(0, total, batch_size):
            batch = rows[i:i + batch_size]
            session.execute_write(_load_batch, batch)
            print(f"   Завантажено {min(i + batch_size, total)}/{total}")


def print_summary(driver):
    with driver.session() as session:
        result = session.run("""
            MATCH (o:Observation)-[:OF_SPECIES]->(s:Species)
            RETURN s.name AS species, count(o) AS n
            ORDER BY n DESC
        """)
        print("\n📊 Підсумок у графі:")
        for record in result:
            print(f"   {record['species']}: {record['n']}")

        result = session.run("MATCH (n) RETURN count(n) AS total")
        print(f"\n   Всього нод: {result.single()['total']}")

        result = session.run("MATCH ()-[r]->() RETURN count(r) AS total")
        print(f"   Всього зв'язків: {result.single()['total']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-size", type=int, default=200)
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--excel-path", type=str, default=EXCEL_PATH)
    args = parser.parse_args()

    if not URI or not PASSWORD:
        print("❌ NEO4J_URI або NEO4J_PASSWORD не знайдено в .env")
        sys.exit(1)

    if not os.path.exists(args.excel_path):
        print(f"❌ Файл не знайдено: {args.excel_path}")
        print("   Вкажи правильний шлях через --excel-path або NABU_EXCEL_PATH в .env")
        sys.exit(1)

    sample_size = None if args.full else args.sample_size
    df = load_and_prepare(args.excel_path, sample_size)

    print(f"\n🔌 Підключення до {URI} ...")
    driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
    driver.verify_connectivity()
    print("✅ З'єднання успішне")

    print(f"\n⬆️  Завантаження {len(df)} записів у Neo4j ...")
    load_to_neo4j(driver, df)

    print_summary(driver)
    driver.close()
    print("\n✅ Готово!")


if __name__ == "__main__":
    main()