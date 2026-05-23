import asyncio
import json
import random
from pathlib import Path

from typing import List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx

from bot import (
    get_token, encrypt_payload, get_leaderboard_top,
    BASE_HEADERS, API_KEY, PROXY, HARDCODED_KEY, SCORE_BONUSES, get_proxy,
)

# ---------------------------------------------------------------------------
WALLETS_FILE = Path("wallets.json")
LEADERBOARD_WALLET = "0x2fe20eef11ed9b1b48aed2bc9ad7b3ad203436c9"  # только для фетча лидерборда
app = FastAPI()

# кеш токенов: { wallet_addr: (token, expires_at) }
_token_cache: dict = {}
TOKEN_TTL = 23 * 3600

async def get_cached_token(wallet: str) -> str:
    import time
    entry = _token_cache.get(wallet.lower())
    if entry:
        token, expires_at = entry
        if time.time() < expires_at:
            return token
    async with httpx.AsyncClient(proxy=get_proxy(),timeout=15) as client:
        token = await get_token(client, wallet)
    _token_cache[wallet.lower()] = (token, time.time() + TOKEN_TTL)
    return token

# WebSocket broadcast
clients: list[WebSocket] = []

async def broadcast(msg: dict):
    dead = []
    for ws in clients:
        try:
            await ws.send_json(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        clients.remove(ws)

@app.websocket("/ws")
async def ws_handler(ws: WebSocket):
    await ws.accept()
    clients.append(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        if ws in clients:
            clients.remove(ws)

# ---------------------------------------------------------------------------
# Wallets CRUD

def load_wallets() -> list[dict]:
    if not WALLETS_FILE.exists():
        return []
    return json.loads(WALLETS_FILE.read_text(encoding="utf-8"))

def save_wallets(wallets: list[dict]):
    WALLETS_FILE.write_text(
        json.dumps(wallets, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

@app.get("/api/wallets")
async def api_get_wallets():
    return load_wallets()

class WalletBody(BaseModel):
    wallet: str

class ImportBody(BaseModel):
    wallets: List[str]

@app.post("/api/wallets", status_code=201)
async def api_add_wallet(body: WalletBody):
    addr = body.wallet.strip()
    if not (addr.startswith("0x") and len(addr) == 42):
        raise HTTPException(400, "Невалидный адрес — нужен 0x + 40 hex символов")
    existing = load_wallets()
    if any(w["wallet"].lower() == addr.lower() for w in existing):
        raise HTTPException(409, "Кошелёк уже добавлен")
    existing.append({"wallet": addr})
    save_wallets(existing)
    return {"added": 1, "skipped": 0, "invalid": 0}

@app.post("/api/import")
async def api_import_wallets(body: ImportBody):
    existing = load_wallets()
    existing_set = {w["wallet"].lower() for w in existing}
    added, skipped, invalid = 0, 0, 0
    for raw in body.wallets:
        addr = raw.strip()
        if not (addr.startswith("0x") and len(addr) == 42):
            invalid += 1
            continue
        if addr.lower() in existing_set:
            skipped += 1
            continue
        existing.append({"wallet": addr})
        existing_set.add(addr.lower())
        added += 1
    save_wallets(existing)
    return {"added": added, "skipped": skipped, "invalid": invalid}

@app.delete("/api/wallets/{address}")
async def api_delete_wallet(address: str):
    wallets = [w for w in load_wallets() if w["wallet"].lower() != address.lower()]
    save_wallets(wallets)
    return {"ok": True}

# ---------------------------------------------------------------------------
# Leaderboard

@app.get("/api/leaderboard")
async def api_leaderboard(limit: int = 200):
    try:
        token = await get_cached_token(LEADERBOARD_WALLET)
        results = await get_leaderboard_top(token, n=limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(500, str(e))

# ---------------------------------------------------------------------------
# Core run logic (shared between /api/run and /api/run-top)

async def _do_run(wallet: str, target: int, manual_duration: Optional[int]):
    if manual_duration:
        score = target
        duration = manual_duration
    else:
        score = target + random.randint(-100, 100)
        score = round(score / 10) * 10
        duration = int(score / 13.5) + random.randint(-30, 30)

    await broadcast({"type": "run_started", "wallet": wallet, "score": score})

    try:
        async with httpx.AsyncClient(proxy=get_proxy(),timeout=30) as client:
            token = await get_cached_token(wallet)
            auth_headers = {**BASE_HEADERS, "Authorization": f"Bearer {token}"}

            start_res = await client.post(
                "https://api-pizza-game.dlicom.io/v1/game-session/start",
                headers=auth_headers,
            )
            if not start_res.is_success:
                raise Exception(f"start: HTTP {start_res.status_code}")

            session_id = start_res.json()["session"]["id"]
            await asyncio.sleep(10)

            encrypted = encrypt_payload(
                {"id": session_id, "score": score, "duration": duration},
                wallet, session_id,
            )
            end_res = await client.post(
                "https://api-pizza-game.dlicom.io/v1/game-session/end",
                headers=auth_headers,
                content=json.dumps({"data": encrypted}),
            )
            result = end_res.json()

        await broadcast({
            "type": "run_done",
            "wallet": wallet,
            "score": score,
            "result": result,
        })

    except Exception as e:
        await broadcast({
            "type": "run_error",
            "wallet": wallet,
            "error": str(e),
        })

# ---------------------------------------------------------------------------
# Run sessions

class RunBody(BaseModel):
    wallets: List[str]
    score: int
    duration: Optional[int] = None

@app.post("/api/run")
async def api_run(body: RunBody):
    if not body.wallets:
        raise HTTPException(400, "Нет кошельков")
    if body.score <= 0:
        raise HTTPException(400, "Score должен быть > 0")
    for wallet in body.wallets:
        asyncio.create_task(_do_run(wallet, body.score, body.duration))
    return {"ok": True, "queued": len(body.wallets)}

# ---------------------------------------------------------------------------
# Run-top: автоматически выводит все кошельки в топ

class RunTopBody(BaseModel):
    wallets: Optional[List[str]] = None   # None = все кошельки из wallets.json
    start_rank: int = 0                    # 0 = целимся с позиции #1

@app.post("/api/run-top")
async def api_run_top(body: RunTopBody):
    wallets_data = load_wallets()
    target_wallets = body.wallets if body.wallets is not None else [w["wallet"] for w in wallets_data]

    if not target_wallets:
        raise HTTPException(400, "Нет кошельков")

    # Свежий лидерборд через выделенный кошелёк
    try:
        token = await get_cached_token(LEADERBOARD_WALLET)
        needed = body.start_rank + len(target_wallets) + 5
        top = await get_leaderboard_top(token, n=max(needed, 20))
    except Exception as e:
        raise HTTPException(500, f"Не удалось получить лидерборд: {e}")

    plan = []
    for i, wallet in enumerate(target_wallets):
        pos = body.start_rank + i
        bonus = SCORE_BONUSES[i] if i < len(SCORE_BONUSES) else 200
        current = top[pos]["best_score"] if pos < len(top) else 0
        target_score = current + bonus
        plan.append({
            "wallet": wallet,
            "position": pos + 1,
            "current_score": current,
            "target_score": target_score,
        })
        asyncio.create_task(_do_run(wallet, target_score, None))

    return {"ok": True, "queued": len(plan), "plan": plan}

# ---------------------------------------------------------------------------
# Serve frontend (должен быть последним)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
