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
PROXY = None       # "http://user:pass@ip:port"
TG_BOT_TOKEN = ""  # токен бота от @BotFather
TG_CHAT_ID = ""    # chat_id куда слать уведомления

# score/duration берутся из wallets.json (поля target_score, target_duration)
# ---------------


def encrypt_payload(data: dict, wallet: str, session_id: str, hardcoded_key: str) -> str:
    salt = os.urandom(16)
    iv = os.urandom(12)

    key_input = f"{wallet}:{session_id}:{hardcoded_key}".encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(key_input)

    aesgcm = AESGCM(key)
    plaintext = json.dumps(data).encode()
    encrypted = aesgcm.encrypt(iv, plaintext, None)

    return base64.b64encode(salt + iv + encrypted).decode()


def calc_pizza_score(target_score: int) -> tuple[int, int, int]:
    """
    Симулирует реальную игру: вычисляет кол-во пицц +10 и +50.
    Распределение ~85% обычных, ~15% бонусных.
    Возвращает (final_score, count_10, count_50).
    """
    # рандом ±100, округляем до кратного 10
    score = target_score + random.randint(-100, 100)
    score = round(score / 10) * 10

    x = score // 10  # сколько "единиц по 10"

    # 10*a + 50*b = score  →  a + 5*b = x
    # при доле +50 ~15%: b ≈ x / 10.67
    b = max(0, round((x / 10.67) * random.uniform(0.95, 1.05)))
    a = x - 5 * b

    # защита от отрицательного a
    if a < 0:
        b = x // 5
        a = x - 5 * b

    return score, a, b


async def get_leaderboard_rank(client: httpx.AsyncClient, wallet: str) -> str:
    """Ищет позицию кошелька в лидерборде."""
    try:
        res = await client.get("https://api-pizza-game.dlicom.io/v1/leaderboard")
        if res.status_code == 200:
            data = res.json()
            leaderboard = data.get("leaderboard", data.get("data", []))
            for i, entry in enumerate(leaderboard, 1):
                addr = entry.get("wallet") or entry.get("walletAddress") or entry.get("address", "")
                if addr.lower() == wallet.lower():
                    return f"#{i}"
            return "не найден"
        return f"HTTP {res.status_code}"
    except Exception as e:
        return f"ошибка: {e}"


async def send_tg(message: str):
    """Отправляет уведомление в Telegram через httpx (без доп. зависимостей)."""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        async with httpx.AsyncClient(timeout=10) as tg:
            await tg.post(url, json={
                "chat_id": TG_CHAT_ID,
                "text": message,
                "parse_mode": "HTML",
            })
    except Exception as e:
        print(f"[TG] ошибка отправки: {e}")


def fmt_time(secs: int) -> str:
    m, s = divmod(secs, 60)
    return f"{m}:{s:02d}"


def short_wallet(wallet: str) -> str:
    return f"{wallet[:6]}...{wallet[-4:]}"


async def run_wallet(idx: int, wallet: str, token: str, target: dict):
    """Запускает одну игровую сессию для кошелька."""
    label = f"[#{idx+1} {short_wallet(wallet)}]"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Ngrok-Skip-Browser-Warning": "true",
        "Origin": "https://pizza.dlicom.io",
        "Referer": "https://pizza.dlicom.io/",
    }

    try:
        async with httpx.AsyncClient(proxy=PROXY, headers=headers, timeout=30) as client:
            # старт сессии
            start_res = await client.post("https://api-pizza-game.dlicom.io/v1/game-session/start")
            if start_res.status_code != 200:
                raise Exception(f"start failed: HTTP {start_res.status_code} — {start_res.text[:200]}")

            session_id = start_res.json()["session"]["id"]
            print(f"{label} сессия: {session_id}")

            # реалистичный score + duration
            score, count_10, count_50 = calc_pizza_score(target["score"])
            duration = target["duration"] + random.randint(-30, 30)
            total_pizzas = count_10 + count_50

            print(f"{label} score={score}, duration={duration}s ({fmt_time(duration)})")
            print(f"{label} пицц: {total_pizzas} шт ({count_10}×+10, {count_50}×+50)")
            print(f"{label} ждём {fmt_time(duration)}...")

            await asyncio.sleep(duration)

            # шифруем и отправляем результат
            encrypted = encrypt_payload(
                {"id": session_id, "score": score, "duration": duration},
                wallet, session_id, HARDCODED_KEY
            )

            end_res = await client.post(
                "https://api-pizza-game.dlicom.io/v1/game-session/end",
                content=json.dumps({"data": encrypted})
            )
            result = end_res.json()
            print(f"{label} ответ сервера: {result}")

            # позиция в лидерборде
            rank = await get_leaderboard_rank(client, wallet)
            print(f"{label} лидерборд: {rank}")

            await send_tg(
                f"🍕 <b>Кошелёк #{idx+1} завершён</b>\n\n"
                f"📊 Score: <b>{score:,}</b>\n"
                f"⏱ Время: {duration} сек ({fmt_time(duration)})\n"
                f"🍕 Пицц: {total_pizzas} шт ({count_10}×+10, {count_50}×+50)\n"
                f"🆔 Session: <code>{session_id[:20]}...</code>\n\n"
                f"🏆 Лидерборд: <b>{rank}</b>\n"
                f"👛 <code>{wallet}</code>"
            )

    except Exception as e:
        print(f"{label} ❌ ошибка: {e}")
        await send_tg(
            f"❌ <b>Кошелёк #{idx+1} — ошибка</b>\n\n"
            f"💥 {e}\n"
            f"👛 <code>{wallet}</code>"
        )


async def main():
    with open("wallets.json", "r") as f:
        wallets = json.load(f)

    print(f"🍕 Запускаем {len(wallets)} сессий параллельно...\n")

    await asyncio.gather(*[
        run_wallet(i, w["wallet"], w["token"], {
            "score": 0,
            "duration": 0,
        })
        for i, w in enumerate(wallets)
    ])

    print("\n✅ Все сессии завершены.")


asyncio.run(main())
