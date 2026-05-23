import asyncio
import base64
import json
import os
import random
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import httpx

# --- конфиг ---
HARDCODED_KEY = "431d2071225ef024356161fe295a1b1c55aa449c599c844607ebc291259e099aca5be1cb39683ac0f4ab5a2bf3cd8b61"
API_KEY = "$2a$12$PxzudDtnM61RKttX18F.8.XuNPSNa8EkrPvz7iyH1QBef9otHAjUm"

PROXY = None

def get_proxy():
    return None

# бонусы к score относительно текущего топа
# индекс = место в топе (0 = #1), значение = сколько прибавить
SCORE_BONUSES = [300, 500, 500, 500, 400, 300, 200]
# ---------------

BASE_HEADERS = {
    "Content-Type": "application/json",
    "Ngrok-Skip-Browser-Warning": "true",
    "Origin": "https://pizza.dlicom.io",
    "Referer": "https://pizza.dlicom.io/",
}


def encrypt_payload(data: dict, wallet: str, session_id: str) -> str:
    salt = os.urandom(16)
    iv = os.urandom(12)
    key_input = f"{wallet}:{session_id}:{HARDCODED_KEY}".encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(key_input)
    aesgcm = AESGCM(key)
    encrypted = aesgcm.encrypt(iv, json.dumps(data).encode(), None)
    return base64.b64encode(salt + iv + encrypted).decode()


def short(wallet: str) -> str:
    return f"{wallet[:6]}...{wallet[-4:]}"


def fmt_time(secs: int) -> str:
    m, s = divmod(secs, 60)
    return f"{m}:{s:02d}"


async def get_token(client: httpx.AsyncClient, wallet: str) -> str:
    res = await client.post(
        "https://api-pizza-game.dlicom.io/v1/auth",
        headers={**BASE_HEADERS, "x-api-key": API_KEY},
        content=json.dumps({"address": wallet}),
    )
    if not res.is_success:
        raise Exception(f"auth failed: HTTP {res.status_code} — {res.text[:200]}")
    body = res.json()
    access = body.get("tokens", {}).get("access", {})
    token = access.get("token") if isinstance(access, dict) else access
    if not token:
        raise Exception(f"auth: не найден токен в ответе: {res.text[:200]}")
    return token


async def check_registered(client: httpx.AsyncClient, wallet: str) -> bool:
    try:
        token = await get_token(client, wallet)
        return bool(token)
    except Exception:
        return False


async def get_leaderboard_top(token: str, n: int = 10) -> list[dict]:
    """Возвращает топ N записей лидерборда."""
    async with httpx.AsyncClient(proxy=get_proxy(),timeout=15) as client:
        res = await client.get(
            f"https://api-pizza-game.dlicom.io/v1/users/leaderboard?page=1&limit={n}",
            headers={
                **BASE_HEADERS,
                "Authorization": f"Bearer {token}",
            },
        )
        if not res.is_success:
            raise Exception(f"leaderboard failed: HTTP {res.status_code} — {res.text[:200]}")
        results = res.json()["data"]["results"]
        return results[:n]


def print_plan(top: list[dict], wallets: list[str], targets: list[int]):
    """Выводит таблицу: текущий топ и план после запуска."""
    n = len(targets)
    print("\n" + "─" * 72)
    print(f"{'#':<5} {'текущий адрес':<20} {'текущий score':>14}  {'→  новый score':>14}")
    print("─" * 72)
    for i in range(n):
        current = top[i] if i < len(top) else {}
        cur_addr = short(current.get("address", "—"))
        cur_score = current.get("best_score", "—")
        new_score = targets[i]
        wallet_lbl = short(wallets[i])
        print(f"#{i+1:<4} {cur_addr:<20} {str(cur_score):>14}  →  {new_score:>12,}  ({wallet_lbl})")
    print("─" * 72 + "\n")


async def run_wallet(idx: int, wallet: str, target_score: int):
    label = f"[#{idx+1} {short(wallet)}]"

    score = target_score + random.randint(-100, 100)
    score = 0
    duration = 0

    try:
        async with httpx.AsyncClient(proxy=get_proxy(),timeout=30) as client:
            token = await get_token(client, wallet)
            print(f"{label} токен получен")

            auth_headers = {**BASE_HEADERS, "Authorization": f"Bearer {token}"}

            start_res = await client.post(
                "https://api-pizza-game.dlicom.io/v1/game-session/start",
                headers=auth_headers,
            )
            if not start_res.is_success:
                raise Exception(f"start failed: HTTP {start_res.status_code} — {start_res.text[:200]}")

            session_id = start_res.json()["session"]["id"]
            print(f"{label} сессия: {session_id}")
            print(f"{label} score={score:,}, duration={duration}s ({fmt_time(duration)})")

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
            print(f"{label} ✅ результат: {result}")

    except Exception as e:
        print(f"{label} ❌ ошибка: {e}")


async def main():
    with open("wallets.json", "r") as f:
        raw = json.load(f)

    wallets = [w["wallet"] for w in raw]

    # 1. проверка регистрации
    print("🔍 Проверяем регистрацию кошельков...\n")
    async with httpx.AsyncClient(proxy=get_proxy(),timeout=15) as client:
        reg_results = await asyncio.gather(*[
            check_registered(client, w) for w in wallets
        ])

    not_registered = [wallets[i] for i, ok in enumerate(reg_results) if not ok]
    if not_registered:
        print("❌ Следующие кошельки не зарегистрированы:\n")
        for w in not_registered:
            print(f"   {w}")
        print("\nЗарегистрируй их на https://pizza.dlicom.io и повтори запуск.")
        return

    print(f"✅ Все {len(wallets)} кошельков зарегистрированы.\n")

    # 2. получаем токен первого кошелька для лидерборда
    async with httpx.AsyncClient(proxy=get_proxy(),timeout=15) as client:
        first_token = await get_token(client, wallets[0])

    # 3. получаем топ лидерборда
    print("📊 Получаем лидерборд...\n")
    n = len(wallets)
    top = await get_leaderboard_top(first_token, n=max(n, 10))

    # 4. считаем target_score для каждого кошелька
    targets = []
    for i in range(n):
        bonus = SCORE_BONUSES[i] if i < len(SCORE_BONUSES) else 200
        current_score = top[i]["best_score"] if i < len(top) else 0
        targets.append(current_score + bonus)

    # 5. таблица плана
    print_plan(top, wallets, targets)

    # 6. подтверждение
    confirm = input("Запустить бота? (y/n): ").strip().lower()
    if confirm != "y":
        print("Отменено.")
        return

    print(f"\n🍕 Запускаем {n} сессий параллельно...\n")

    await asyncio.gather(*[
        run_wallet(i, wallets[i], targets[i])
        for i in range(n)
    ])

    print("\n✅ Все сессии завершены.")


if __name__ == "__main__":
    asyncio.run(main())
