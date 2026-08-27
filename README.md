# 福清找房地图

一个电脑优先的福清主城区个人找房工作台。首期使用本地示例数据，支持小区搜索、片区筛选、价格口径切换、POI 图层、价格趋势、收藏、标签、笔记、片区绘制和 JSON/CSV 导入。

## 启动

```powershell
npm install
npm run dev
```

可选地启动本地 API（用于 SQLite 持久化）：

```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn main:app --reload --port 8000
```

前端默认地址为 `http://localhost:5173`。使用前必须在根目录 `.env` 中配置高德地图 Key 与安全密钥（`VITE_AMAP_KEY` 和 `VITE_AMAP_SECURITY_CODE`，平台类型须为 **Web端 (JS API)**），未配置时系统将拦截使用。

## 导入格式

JSON 可以是小区数组，也可以是 `{ "communities": [] }`。最小字段如下：

```json
{
  "id": "fq_demo_001",
  "name": "示例小区",
  "plate": "音西万达片区",
  "center": [119.38, 25.72],
  "listingPrice": 12000,
  "transactionPrice": 11000,
  "listingCount": 12,
  "lastUpdated": "2026-08-25",
  "source": "手动整理",
  "snapshots": [
    { "metric": "listing", "value": 12000, "capturedAt": "2026-08-25" }
  ]
}
```

CSV 表头支持 `id,name,plate,lng,lat,listingPrice,transactionPrice,listingCount`。导入会按小区 ID 或名称更新基础信息，并通过 `community_id + metric + value + captured_at + source` 避免重复历史快照。
