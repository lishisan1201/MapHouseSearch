from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("FQ_DB_PATH", str(ROOT / "backend" / "fuqing.db")))
SEED_PATH = ROOT / "shared" / "demo-data.json"


def init_schema(connection: sqlite3.Connection) -> None:
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS communities (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            plate TEXT NOT NULL,
            center_lng REAL NOT NULL,
            center_lat REAL NOT NULL,
            listing_price REAL NOT NULL DEFAULT 0,
            transaction_price REAL NOT NULL DEFAULT 0,
            listing_count INTEGER NOT NULL DEFAULT 0,
            build_year INTEGER NOT NULL DEFAULT 0,
            developer TEXT NOT NULL DEFAULT '',
            property_company TEXT NOT NULL DEFAULT '',
            tags_json TEXT NOT NULL DEFAULT '[]',
            last_updated TEXT NOT NULL DEFAULT '',
            source TEXT NOT NULL DEFAULT '',
            note TEXT NOT NULL DEFAULT '',
            favorite INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS price_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            community_id TEXT NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
            metric TEXT NOT NULL CHECK(metric IN ('listing', 'transaction')),
            value REAL NOT NULL,
            captured_at TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT '',
            sample_count INTEGER NOT NULL DEFAULT 0,
            source_url TEXT NOT NULL DEFAULT '',
            UNIQUE(community_id, metric, value, captured_at, source)
        );
        CREATE TABLE IF NOT EXISTS areas (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            color TEXT NOT NULL,
            min_zoom REAL NOT NULL,
            max_zoom REAL NOT NULL,
            center_lng REAL NOT NULL,
            center_lat REAL NOT NULL,
            polygon_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS pois (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            center_lng REAL NOT NULL,
            center_lat REAL NOT NULL,
            subtitle TEXT NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_price_snapshots_community ON price_snapshots(community_id, metric, captured_at);
        """
    )
    connection.commit()


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    init_schema(connection)
    return connection


def _value(record: dict[str, Any], camel: str, snake: str, default: Any = None) -> Any:
    return record.get(camel, record.get(snake, default))


def latest_price(snapshots: list[dict[str, Any]], metric: str) -> dict[str, Any] | None:
    matching = [
        snapshot for snapshot in snapshots
        if snapshot.get("metric") == metric and float(snapshot.get("value", 0)) > 0
    ]
    return max(matching, key=lambda snapshot: str(snapshot.get("capturedAt", snapshot.get("captured_at", ""))), default=None)


def _normalise_snapshot(snapshot: dict[str, Any], source: str) -> tuple[str, float, str, str, int, str]:
    metric = str(snapshot.get("metric", "listing"))
    if metric not in {"listing", "transaction"}:
        metric = "listing"
    value = float(snapshot.get("value", 0))
    captured_at = str(snapshot.get("capturedAt", snapshot.get("captured_at", "")))
    return metric, value, captured_at, str(snapshot.get("source", source)), int(snapshot.get("sampleCount", snapshot.get("sample_count", 0))), str(snapshot.get("sourceUrl", snapshot.get("source_url", "")))


def import_communities(connection: sqlite3.Connection, records: list[dict[str, Any]]) -> int:
    init_schema(connection)
    changed = 0
    for record in records:
        community_id = str(_value(record, "id", "community_id", ""))
        if not community_id:
            continue
        center = _value(record, "center", "center_coord", None) or [float(record.get("lng", 119.38)), float(record.get("lat", 25.72))]
        tags = _value(record, "tags", "tags", []) or []
        snapshots = record.get("snapshots", record.get("history_prices", [])) or []
        source = str(record.get("source", "手动导入"))
        listing_snapshot = latest_price(snapshots, "listing")
        transaction_snapshot = latest_price(snapshots, "transaction")
        listing_price = float(_value(record, "listingPrice", "current_price", listing_snapshot.get("value", 0) if listing_snapshot else 0) or 0)
        transaction_price = float(_value(record, "transactionPrice", "transaction_price", transaction_snapshot.get("value", 0) if transaction_snapshot else 0) or 0)
        values = (
            community_id,
            str(record.get("name", "未命名小区")),
            str(record.get("plate", record.get("district", "未分片区"))),
            float(center[0]),
            float(center[1]),
            listing_price,
            transaction_price,
            int(_value(record, "listingCount", "listing_count", record.get("listings", 0)) or 0),
            int(record.get("buildYear", record.get("build_year", 0)) or 0),
            str(record.get("developer", "")),
            str(record.get("propertyCompany", record.get("property_company", ""))),
            json.dumps([str(tag) for tag in tags], ensure_ascii=False),
            str(record.get("lastUpdated", record.get("last_updated", ""))),
            source,
            str(record.get("note", record.get("user_notes", ""))),
            1 if record.get("favorite", False) else 0,
        )
        connection.execute(
            """
            INSERT INTO communities (id, name, plate, center_lng, center_lat, listing_price, transaction_price, listing_count, build_year, developer, property_company, tags_json, last_updated, source, note, favorite)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              name=excluded.name, plate=excluded.plate, center_lng=excluded.center_lng, center_lat=excluded.center_lat,
              listing_price=excluded.listing_price, transaction_price=excluded.transaction_price, listing_count=excluded.listing_count,
              build_year=excluded.build_year, developer=excluded.developer, property_company=excluded.property_company,
              tags_json=excluded.tags_json, last_updated=excluded.last_updated, source=excluded.source, note=excluded.note
            """,
            values,
        )
        for snapshot in snapshots:
            metric, value, captured_at, snapshot_source, sample_count, source_url = _normalise_snapshot(snapshot, source)
            if value <= 0 or not captured_at:
                continue
            connection.execute(
                "INSERT OR IGNORE INTO price_snapshots (community_id, metric, value, captured_at, source, sample_count, source_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (community_id, metric, value, captured_at, snapshot_source, sample_count, source_url),
            )
        changed += 1
    connection.commit()
    return changed


def _community_dict(connection: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
    snapshots = connection.execute(
        "SELECT metric, value, captured_at, source, sample_count, source_url FROM price_snapshots WHERE community_id = ? ORDER BY captured_at",
        (row["id"],),
    ).fetchall()
    return {
        "id": row["id"], "name": row["name"], "plate": row["plate"], "center": [row["center_lng"], row["center_lat"]],
        "listingPrice": row["listing_price"], "transactionPrice": row["transaction_price"], "listingCount": row["listing_count"],
        "buildYear": row["build_year"], "developer": row["developer"], "propertyCompany": row["property_company"],
        "tags": json.loads(row["tags_json"] or "[]"), "lastUpdated": row["last_updated"], "source": row["source"],
        "note": row["note"], "favorite": bool(row["favorite"]),
        "snapshots": [{"metric": item["metric"], "value": item["value"], "capturedAt": item["captured_at"], "source": item["source"], "sampleCount": item["sample_count"], "sourceUrl": item["source_url"]} for item in snapshots],
    }


def _areas(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute("SELECT * FROM areas ORDER BY name").fetchall()
    return [{"id": row["id"], "name": row["name"], "type": row["type"], "color": row["color"], "minZoom": row["min_zoom"], "maxZoom": row["max_zoom"], "center": [row["center_lng"], row["center_lat"]], "polygon": json.loads(row["polygon_json"])} for row in rows]


def _pois(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute("SELECT * FROM pois ORDER BY category, name").fetchall()
    return [{"id": row["id"], "name": row["name"], "category": row["category"], "center": [row["center_lng"], row["center_lat"]], "subtitle": row["subtitle"]} for row in rows]


def seed_database(connection: sqlite3.Connection) -> None:
    if connection.execute("SELECT COUNT(*) FROM communities").fetchone()[0] > 0:
        return
    if not SEED_PATH.exists():
        return
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    import_communities(connection, data.get("communities", []))
    for area in data.get("areas", []):
        connection.execute("INSERT OR IGNORE INTO areas (id, name, type, color, min_zoom, max_zoom, center_lng, center_lat, polygon_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (area["id"], area["name"], area["type"], area["color"], area["minZoom"], area["maxZoom"], area["center"][0], area["center"][1], json.dumps(area["polygon"])))
    for poi in data.get("pois", []):
        connection.execute("INSERT OR IGNORE INTO pois (id, name, category, center_lng, center_lat, subtitle) VALUES (?, ?, ?, ?, ?, ?)", (poi["id"], poi["name"], poi["category"], poi["center"][0], poi["center"][1], poi["subtitle"]))
    connection.commit()


def initialize_database() -> None:
    connection = get_connection()
    seed_database(connection)
    connection.close()


app = FastAPI(title="Fuqing House Map API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def on_startup() -> None:
    initialize_database()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/map")
def map_data(q: str | None = Query(default=None), bbox: str | None = Query(default=None)) -> dict[str, Any]:
    connection = get_connection()
    rows = connection.execute("SELECT * FROM communities ORDER BY listing_count DESC").fetchall()
    communities = [_community_dict(connection, row) for row in rows]
    if q:
        query = q.casefold()
        communities = [item for item in communities if query in f"{item['name']} {item['plate']} {' '.join(item['tags'])}".casefold()]
    if bbox:
        try:
            min_lng, min_lat, max_lng, max_lat = [float(value) for value in bbox.split(",")]
            communities = [item for item in communities if min_lng <= item["center"][0] <= max_lng and min_lat <= item["center"][1] <= max_lat]
        except ValueError:
            raise HTTPException(status_code=400, detail="bbox 必须是 minLng,minLat,maxLng,maxLat")
    result = {"areas": _areas(connection), "communities": communities, "pois": _pois(connection)}
    connection.close()
    return result


@app.get("/api/communities/{community_id}")
def community_detail(community_id: str) -> dict[str, Any]:
    connection = get_connection()
    row = connection.execute("SELECT * FROM communities WHERE id = ?", (community_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="小区不存在")
    result = _community_dict(connection, row)
    connection.close()
    return result


@app.get("/api/communities/{community_id}/prices")
def community_prices(community_id: str) -> dict[str, Any]:
    detail = community_detail(community_id)
    return {"communityId": community_id, "prices": detail["snapshots"], "latest": {"listing": latest_price(detail["snapshots"], "listing"), "transaction": latest_price(detail["snapshots"], "transaction")}}


@app.post("/api/imports")
def import_data(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    records = payload.get("communities", payload if isinstance(payload, list) else [])
    if not isinstance(records, list):
        raise HTTPException(status_code=400, detail="communities 必须是数组")
    connection = get_connection()
    count = import_communities(connection, records)
    connection.close()
    return {"imported": count, "mode": "manual", "message": "数据已写入，历史快照已保留"}


@app.post("/api/communities/{community_id}/refresh")
def refresh_community(community_id: str) -> dict[str, Any]:
    detail = community_detail(community_id)
    return {"status": "manual_required", "communityId": community_id, "lastUpdated": detail["lastUpdated"], "message": "暂无自动采集源，请导入最新 JSON / CSV 数据。"}


@app.patch("/api/communities/{community_id}/personal")
def update_personal(community_id: str, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    connection = get_connection()
    if not connection.execute("SELECT 1 FROM communities WHERE id = ?", (community_id,)).fetchone():
        raise HTTPException(status_code=404, detail="小区不存在")
    updates: list[str] = []
    values: list[Any] = []
    if "note" in payload:
        updates.append("note = ?"); values.append(str(payload["note"]))
    if "favorite" in payload:
        updates.append("favorite = ?"); values.append(1 if payload["favorite"] else 0)
    if "tags" in payload and isinstance(payload["tags"], list):
        updates.append("tags_json = ?"); values.append(json.dumps([str(tag) for tag in payload["tags"]], ensure_ascii=False))
    if updates:
        values.append(community_id)
        connection.execute(f"UPDATE communities SET {', '.join(updates)} WHERE id = ?", values)
        connection.commit()
    row = connection.execute("SELECT * FROM communities WHERE id = ?", (community_id,)).fetchone()
    result = _community_dict(connection, row)
    connection.close()
    return result


@app.get("/api/areas")
def get_areas() -> list[dict[str, Any]]:
    connection = get_connection(); result = _areas(connection); connection.close(); return result


@app.post("/api/areas")
def create_area(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    polygon = payload.get("polygon", [])
    if not isinstance(polygon, list) or len(polygon) < 3:
        raise HTTPException(status_code=400, detail="片区至少需要 3 个边界点")
    center = payload.get("center") or [sum(point[0] for point in polygon) / len(polygon), sum(point[1] for point in polygon) / len(polygon)]
    area = {"id": str(payload.get("id", f"custom-{int(__import__('time').time() * 1000)}")), "name": str(payload.get("name", "未命名片区")), "type": "custom", "color": str(payload.get("color", "#2f6df6")), "minZoom": float(payload.get("minZoom", 10)), "maxZoom": float(payload.get("maxZoom", 12.5)), "center": center, "polygon": polygon}
    connection = get_connection()
    connection.execute("INSERT OR REPLACE INTO areas (id, name, type, color, min_zoom, max_zoom, center_lng, center_lat, polygon_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (area["id"], area["name"], area["type"], area["color"], area["minZoom"], area["maxZoom"], center[0], center[1], json.dumps(polygon)))
    connection.commit(); connection.close()
    return area


if __name__ == "__main__":
    initialize_database()
