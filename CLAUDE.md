# dlicom pizza game score bot

## контекст
веб игра на https://pizza.dlicom.io — падают пиццы, собираешь очки (+10/+50), есть лидерборд с бэком.

## стек
- фронт: react + zustand, игра на DOM элементах (canvas: null)
- бэк: https://api-pizza-game.dlicom.io
- шифрование: PBKDF2 (100000 iterations, SHA-256) + AES-GCM (256bit)

## api endpoints
- `POST /v1/game-session/start` — старт сессии, возвращает `session.id`
- `POST /v1/game-session/end` — конец сессии, body: `{ data: "<encrypted>" }`

## схема шифрования
```js
// ключ дерайвится из:
// `${walletAddr}:${sessionId}:${hardcodedKey}`
// через PBKDF2, salt = random 16 bytes

// payload шифруется AES-GCM:
// итоговый буфер = salt(16) + iv(12) + encrypted
// затем btoa()
```

## константы
```
hardcoded_key = "431d2071225ef024356161fe295a1b1c55aa449c599c844607ebc291259e099aca5be1cb39683ac0f4ab5a2bf3cd8b61"
pbkdf2 iterations = 100000
hash = SHA-256
key length = 256 bit
```

## авторизация
- bearer токен из куки `at=` (живёт 30 дней)
- wallet address из куки `add=`
- обязательный header: `Ngrok-Skip-Browser-Warning: true`

## логика score/duration
- пиццы дают +10 или +50 очков
- реалистичный диапазон: duration 280-420 сек, score ~3800-5700
- формула: `base_score = duration * 13.5`, затем ±100 рандом

## рабочий питон скрипт
файл `bot.py` — использует `httpx` + `cryptography`
- поддержка прокси через параметр `PROXY`
- ждёт реальное время duration перед отправкой (антипалево)

```python
import asyncio
import base64
import json
import os
import random
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import httpx

# --- вставь свои данные ---
WALLET = "0xdF24872c1a0B65f32b639d783A2fc94F452A4a1a"
AUTH_TOKEN = "eyJhbGci..."  # кука at=
HARDCODED_KEY = "431d2071225ef024356161fe295a1b1c55aa449c599c844607ebc291259e099aca5be1cb39683ac0f4ab5a2bf3cd8b61"
PROXY = None  # например "http://user:pass@ip:port"
# --------------------------

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

    result = salt + iv + encrypted
    return base64.b64encode(result).decode()

async def run():
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json",
        "Ngrok-Skip-Browser-Warning": "true",
        "Origin": "https://pizza.dlicom.io",
        "Referer": "https://pizza.dlicom.io/",
    }

    async with httpx.AsyncClient(proxy=PROXY, headers=headers) as client:
        start_res = await client.post("https://api-pizza-game.dlicom.io/v1/game-session/start")
        session_data = start_res.json()
        session_id = session_data["session"]["id"]
        print(f"session id: {session_id}")

        duration = random.randint(280, 420)
        base_score = int(duration * 13.5)
        score = base_score + random.randint(-100, 100)
        print(f"score: {score}, duration: {duration}s")

        print(f"ждём {duration} секунд...")
        await asyncio.sleep(duration)

        encrypted = encrypt_payload(
            {"id": session_id, "score": score, "duration": duration},
            WALLET, session_id, HARDCODED_KEY
        )

        end_res = await client.post(
            "https://api-pizza-game.dlicom.io/v1/game-session/end",
            content=json.dumps({"data": encrypted})
        )
        result = end_res.json()
        print(f"результат: {result}")

asyncio.run(run())
```

## зависимости
```bash
pip install httpx cryptography
```

## что сделано
- [x] реверс инжиниринг шифрования из минифицированного js
- [x] рабочий js скрипт для браузерной консоли
- [x] рабочий питон скрипт с поддержкой прокси
- [x] валидация на сервере проходит успешно

## что можно улучшить
- [ ] автообновление токена (сейчас вручную копировать из браузера)
- [ ] запуск нескольких сессий подряд в цикле
- [ ] более реалистичная кривая score (комбо, разные типы пицц)
- [ ] телеграм уведомления о результатах
