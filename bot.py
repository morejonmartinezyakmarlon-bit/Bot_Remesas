import asyncio
import logging
import os
import aiohttp
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from telethon import Button, TelegramClient, events
from pathlib import Path

load_dotenv()

logging.basicConfig(level=logging.INFO)

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')

client = TelegramClient('bot_session', API_ID, API_HASH)

ADMIN_CHAT_ID = 1425847313  # Cambia por el ID real del admin

user_states = {}
FILES_DIR = Path("files")
FILES_DIR.mkdir(exist_ok=True)

BASE_URL = "https://botremesasapi-production.up.railway.app"

# --------------------------------------------------------------
# Funciones de API (sin cambios)
# --------------------------------------------------------------
async def verificar_admin(user_telegram_id: int):
    url = f"{BASE_URL}/api/admin"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    admins = await resp.json()
                    for admin in admins:
                        if admin.get("idUserTelegram") == user_telegram_id:
                            return True, admin.get("id")
                    return False, None
                return False, None
    except Exception as e:
        logging.error(f"Error en verificar_admin: {e}")
        return False, None

async def listar_usuarios():
    url = f"{BASE_URL}/api/user"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    except Exception as e:
        logging.error(f"Error en listar_usuarios: {e}")
        return None

async def obtener_usuario_por_telegram_id(telegram_id: int):
    usuarios = await listar_usuarios()
    if not usuarios:
        return None
    for u in usuarios:
        if u.get("idUserTelegram") == telegram_id:
            return u
    return None

async def obtener_usuario_por_uuid(user_uuid: str):
    if not user_uuid:
        return None
    usuarios = await listar_usuarios()
    if not usuarios:
        return None
    for u in usuarios:
        if u.get("id") == user_uuid:
            return u
    return None

async def crear_usuario(name: str, id_user_telegram: int, admin_id: str, per_cent: float = 0.0):
    url = f"{BASE_URL}/api/user"
    payload = {
        "name": name,
        "idUserTelegram": id_user_telegram,
        "adminId": admin_id,
        "perCent": per_cent
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status in (200, 201):
                    await asyncio.sleep(0.5)
                    usuario = await obtener_usuario_por_telegram_id(id_user_telegram)
                    if usuario and usuario.get("id"):
                        return True, "✅ Usuario creado correctamente.", usuario["id"]
                    else:
                        return True, "⚠️ Usuario creado, pero no se pudo obtener su ID.", None
                texto = await resp.text()
                return False, f"❌ Error al crear usuario: {resp.status} - {texto}", None
    except Exception as e:
        return False, f"❌ Error de conexión: {e}", None

async def crear_pay(user_id: str):
    url = f"{BASE_URL}/api/pay"
    payload = {"userId": user_id}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status in (200, 201):
                    return True, "✅ Pago registrado correctamente."
                texto = await resp.text()
                return False, f"❌ Error al registrar pago: {resp.status} - {texto}"
    except Exception as e:
        return False, f"❌ Error de conexión en pago: {e}"

async def actualizar_usuario(user_id: str, name: str, id_user_telegram: int, per_cent: float):
    url = f"{BASE_URL}/api/user"
    payload = {
        "id": user_id,
        "name": name,
        "idUserTelegram": id_user_telegram,
        "perCent": per_cent
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.put(url, json=payload) as resp:
                if resp.status in (200, 204):
                    return True, "✅ Usuario actualizado correctamente."
                texto = await resp.text()
                return False, f"❌ Error al actualizar usuario: {resp.status} - {texto}"
    except Exception as e:
        return False, f"❌ Error de conexión: {e}"

async def eliminar_usuario(user_uuid: str):
    url = f"{BASE_URL}/api/user/{user_uuid}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(url) as resp:
                if resp.status in (200, 204):
                    return True, "✅ Usuario eliminado correctamente."
                texto = await resp.text()
                return False, f"❌ Error al eliminar usuario: {resp.status} - {texto}"
    except Exception as e:
        return False, f"❌ Error de conexión: {e}"

async def crear_remesa(user_id: str, amount: float, customer: str, url_image: str, account_id: str):
    url = f"{BASE_URL}/api/Remittance"
    payload = {
        "userId": user_id,
        "amount": amount,
        "customer": customer,
        "urlImage": url_image,
        "accountId": account_id
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status in (200, 201):
                    return True, "✅ Remesa creada correctamente."
                texto = await resp.text()
                return False, f"❌ Error al crear remesa: {resp.status} - {texto}"
    except Exception as e:
        return False, f"❌ Error de conexión: {e}"

async def listar_remesas():
    url = f"{BASE_URL}/api/Remittance"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    except Exception as e:
        logging.error(f"Error en listar_remesas: {e}")
        return None

async def listar_history_remittances(user_id: str):
    url = f"{BASE_URL}/api/historyRemittance/{user_id}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    except Exception as e:
        logging.error(f"Error en listar_history_remittances: {e}")
        return None

async def actualizar_remesa(remesa_id: str, amount: float, url_image: str, address: str, user_id: str, admin_id: str, enabled: bool = None):
    url = f"{BASE_URL}/api/Remittance"
    payload = {
        "id": remesa_id,
        "amount": amount,
        "urlImage": url_image,
        "address": address,
        "userId": user_id,
        "adminId": admin_id
    }
    if enabled is not None:
        payload["enabled"] = enabled
    try:
        async with aiohttp.ClientSession() as session:
            async with session.put(url, json=payload) as resp:
                if resp.status in (200, 204):
                    return True, "✅ Remesa actualizada correctamente."
                texto = await resp.text()
                return False, f"❌ Error al actualizar remesa: {resp.status} - {texto}"
    except Exception as e:
        return False, f"❌ Error de conexión: {e}"

async def confirmar_remesa(remesa_id: str, admin_id: str):
    url = f"{BASE_URL}/api/Remittance"
    payload = {
        "id": remesa_id,
        "adminId": admin_id,
        "amount": None,
        "urlImage": None,
        "address": None,
        "userId": None,
        "enabled": True
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.put(url, json=payload) as resp:
                if resp.status in (200, 204):
                    return True, "✅ Remesa confirmada correctamente."
                texto = await resp.text()
                return False, f"❌ Error al confirmar remesa: {resp.status} - {texto}"
    except Exception as e:
        return False, f"❌ Error de conexión: {e}"

async def eliminar_remesa(remesa_id: str):
    url = f"{BASE_URL}/api/Remittance/{remesa_id}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(url) as resp:
                if resp.status in (200, 204):
                    return True, "✅ Remesa eliminada correctamente."
                texto = await resp.text()
                return False, f"❌ Error al eliminar remesa: {resp.status} - {texto}"
    except Exception as e:
        return False, f"❌ Error de conexión: {e}"

async def listar_pagos():
    url = f"{BASE_URL}/api/pay"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    except Exception as e:
        logging.error(f"Error en listar_pagos: {e}")
        return None

async def actualizar_pago(pago_id: str, user_id: str, amount: float, enabled_sum: bool = True):
    url = f"{BASE_URL}/api/pay"
    payload = {
        "id": pago_id,
        "userId": user_id,
        "amount": amount,
        "enabledSum": enabled_sum
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.put(url, json=payload) as resp:
                if resp.status in (200, 204):
                    return True, "✅ Saldo del usuario actualizado correctamente."
                texto = await resp.text()
                return False, f"❌ Error al actualizar saldo: {resp.status} - {texto}"
    except Exception as e:
        return False, f"❌ Error de conexión: {e}"

async def actualizar_saldo_usuario(user_id: str, monto_remesa: float, enabled_sum: bool = True):
    pagos = await listar_pagos()
    if pagos is None:
        return False, "❌ Error al obtener la lista de pagos."
    pago_usuario = None
    for p in pagos:
        if p.get("userId") == user_id:
            pago_usuario = p
            break
    if not pago_usuario:
        exito_crear, msg_crear = await crear_pay(user_id)
        if exito_crear:
            pagos = await listar_pagos()
            for p in pagos:
                if p.get("userId") == user_id:
                    pago_usuario = p
                    break
            if not pago_usuario:
                return False, "❌ No se pudo recuperar el pago recién creado."
        else:
            if "ya tiene un pago" in msg_crear.lower():
                for _ in range(3):
                    await asyncio.sleep(1)
                    pagos = await listar_pagos()
                    for p in pagos:
                        if p.get("userId") == user_id:
                            pago_usuario = p
                            break
                    if pago_usuario:
                        break
                if not pago_usuario:
                    return False, f"❌ El pago del usuario existe pero no se pudo obtener: {msg_crear}"
            else:
                return False, f"❌ No se pudo crear el pago: {msg_crear}"
    exito, mensaje = await actualizar_pago(pago_usuario["id"], user_id, monto_remesa, enabled_sum)
    return exito, mensaje

async def descargar_imagen(message, user_id: int) -> str:
    if not message.photo:
        return None
    timestamp = asyncio.get_event_loop().time()
    filename = f"{user_id}_{int(timestamp)}.jpg"
    filepath = FILES_DIR / filename
    path = await message.download_media(file=str(filepath))
    return str(path)

async def eliminar_archivo_imagen(ruta: str):
    if ruta and os.path.exists(ruta):
        try:
            os.remove(ruta)
            logging.info(f"Imagen eliminada: {ruta}")
        except Exception as e:
            logging.error(f"Error al eliminar imagen {ruta}: {e}")

# --------------------------------------------------------------
# Funciones para cuentas
# --------------------------------------------------------------
async def listar_cuentas():
    url = f"{BASE_URL}/api/account"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    except Exception as e:
        logging.error(f"Error en listar_cuentas: {e}")
        return None

async def crear_cuenta(account: str, admin_id: str):
    url = f"{BASE_URL}/api/account"
    payload = {"account": account, "adminId": admin_id}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status in (200, 201):
                    return True, "✅ Cuenta creada correctamente."
                texto = await resp.text()
                return False, f"❌ Error al crear cuenta: {resp.status} - {texto}"
    except Exception as e:
        return False, f"❌ Error de conexión: {e}"

async def retirar_saldo(account_id: str, admin_id: str, value: float):
    url = f"{BASE_URL}/api/account"
    payload = {"id": account_id, "adminId": admin_id, "enabledSum": False, "value": value}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.put(url, json=payload) as resp:
                if resp.status in (200, 204):
                    return True, "✅ Retiro realizado correctamente."
                texto = await resp.text()
                return False, f"❌ Error al retirar saldo: {resp.status} - {texto}"
    except Exception as e:
        return False, f"❌ Error de conexión: {e}"

async def actualizar_balance_cuenta(account_id: str, admin_id: str, value: float):
    url = f"{BASE_URL}/api/account"
    payload = {"id": account_id, "adminId": admin_id, "enabledSum": True, "value": value}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.put(url, json=payload) as resp:
                if resp.status in (200, 204):
                    return True, "✅ Saldo de cuenta actualizado correctamente."
                texto = await resp.text()
                return False, f"❌ Error al actualizar saldo de cuenta: {resp.status} - {texto}"
    except Exception as e:
        return False, f"❌ Error de conexión: {e}"

async def crear_history_remittance(user_id: str, account: str, amount: float, customer: str):
    url = f"{BASE_URL}/api/historyRemittance"
    payload = {"userId": user_id, "account": account, "amount": amount, "customer": customer}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status in (200, 201):
                    return True, "✅ Historial de remesa registrado."
                texto = await resp.text()
                return False, f"❌ Error al registrar historial: {resp.status} - {texto}"
    except Exception as e:
        return False, f"❌ Error de conexión al registrar historial: {e}"

# --------------------------------------------------------------
# Funciones auxiliares para mostrar remesas y cuentas
# --------------------------------------------------------------
async def mostrar_remesas(event, remesas, titulo="📋 **Lista de remesas:**"):
    if not remesas:
        await event.reply("📭 No hay remesas para mostrar.")
        return
    await event.reply(titulo)
    for r in remesas:
        texto = (f"**ID:** `{r.get('id')}`\n"
                 f"**Usuario:** {r.get('userName', '?')}\n"
                 f"**Cliente:** {r.get('customer', '?')}\n"
                 f"**Monto:** {r.get('amount')}\n"
                 f"**Cuenta:** {r.get('address', '?')}\n"
                 f"**Habilitada:** {'✅' if r.get('enabled') else '❌'}\n")
        img_path = r.get('urlImage', '')
        if img_path and img_path != "string" and os.path.exists(img_path):
            try:
                await client.send_file(event.chat_id, img_path, caption=texto)
            except Exception as e:
                logging.error(f"Error al enviar imagen: {e}")
                await event.reply(f"{texto}\n⚠️ No se pudo cargar la imagen.")
        else:
            await event.reply(texto)

async def mostrar_cuentas(event, cuentas, titulo="🏦 **Lista de cuentas:**"):
    if not cuentas:
        await event.reply("📭 No hay cuentas registradas.")
        return
    mensaje = f"{titulo}\n\n"
    for c in cuentas:
        mensaje += (f"**Cuenta:** `{c.get('account', '?')}`\n"
                    f"**Saldo:** {c.get('balance', 0)}\n"
                    f"**ID:** `{c.get('id', '?')}`\n\n")
    if len(mensaje) > 4000:
        for i in range(0, len(mensaje), 4000):
            await event.reply(mensaje[i:i+4000])
    else:
        await event.reply(mensaje)

# --------------------------------------------------------------
# Menús principales
# --------------------------------------------------------------
async def send_user_menu(user_id: int):
    botones = [
        [Button.inline("➕ Crear remesa", data="user_create_remesa"),
         Button.inline("👁️ Ver mis remesas", data="user_view_remesas"),
         Button.inline("💰 Ver mi salario", data="user_view_salary")]
    ]
    await client.send_message(user_id, "📦 **Tus remesas**\nSelecciona una acción:", buttons=botones)

async def send_admin_menu(user_id: int):
    mensaje = (
        "¡Hola! Soy el bot de gestión.\n"
        "Usa /user para gestión de usuarios (solo admin).\n"
        "Usa /remesas para gestionar tus remesas y salario.\n"
        "Usa /cuentas para gestionar cuentas bancarias (solo admin)."
    )
    await client.send_message(user_id, mensaje)

# --------------------------------------------------------------
# Handlers de comandos
# --------------------------------------------------------------
@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    user_id = event.sender_id
    es_admin, _ = await verificar_admin(user_id)
    if es_admin:
        await send_admin_menu(user_id)
    else:
        await send_user_menu(user_id)

@client.on(events.NewMessage(pattern='/user'))
async def user_handler(event):
    user_id = event.sender_id
    es_admin, _ = await verificar_admin(user_id)
    if es_admin:
        botones = [
            [Button.inline("✨ Crear usuario", data="createuser"),
             Button.inline("📊 Actualizar porcentaje", data="update_percent")],
            [Button.inline("🗑️ Eliminar usuario", data="deleteuser"),
             Button.inline("👁️ Ver usuarios", data="viewuser")]
        ]
        await event.respond("Selecciona una acción:", buttons=botones)
    else:
        botones = [[Button.inline("✨ Solicitar crear usuario", data="createuser")]]
        await event.respond("Para crear una cuenta, solicita al administrador:", buttons=botones)

@client.on(events.NewMessage(pattern='/remesas'))
async def remesas_handler(event):
    user_id = event.sender_id
    es_admin, _ = await verificar_admin(user_id)
    if es_admin:
        botones = [
            [Button.inline("➕ Crear remesa", data="admin_create_remesa"),
             Button.inline("✏️ Actualizar remesa", data="admin_update_remesa")],
            [Button.inline("👁️ Ver remesas", data="admin_view_remesas"),
             Button.inline("💰 Ver salario", data="admin_view_salary")]
        ]
        await event.respond("📦 **Gestión de remesas y salarios**\nSelecciona una acción:", buttons=botones)
    else:
        usuario = await obtener_usuario_por_telegram_id(user_id)
        if not usuario:
            await event.reply("❌ No tienes una cuenta de usuario registrada. Contacta a un administrador.")
            return
        user_uuid = usuario.get("id")
        if not user_uuid:
            await event.reply("❌ Error: tu usuario no tiene UUID válido.")
            return
        user_states[user_id] = {"user_uuid": user_uuid}
        await send_user_menu(user_id)

@client.on(events.NewMessage(pattern='/cuentas'))
async def cuentas_handler(event):
    user_id = event.sender_id
    es_admin, admin_uuid = await verificar_admin(user_id)
    if not es_admin:
        await event.reply("⛔ Solo administradores pueden acceder a este comando.")
        return
    botones = [
        [Button.inline("➕ Crear cuenta", data="admin_create_account"),
         Button.inline("💸 Retirar saldo", data="admin_withdraw"),
         Button.inline("👁️ Ver cuentas", data="admin_view_accounts")]
    ]
    await event.respond("🏦 **Gestión de cuentas**\nSelecciona una acción:", buttons=botones)

# --------------------------------------------------------------
# Callback principal (solo se modifican los bloques de admin_view_remesas y admin_history_)
# --------------------------------------------------------------
@client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode('utf-8')
    user_id = event.sender_id

    async def safe_answer(text, alert=False):
        try:
            await event.answer(text, alert=alert)
        except Exception as e:
            logging.warning(f"Error al responder callback: {e}")

    # ---------- Selección de cuenta para crear remesa ----------
    if data.startswith("select_account_"):
        account_id = data.replace("select_account_", "")
        if user_id not in user_states:
            await safe_answer("⚠️ Sesión expirada. Vuelve a iniciar el proceso.", alert=True)
            return
        state = user_states[user_id]
        if state.get("step") == "awaiting_account_selection":
            state["selected_account_id"] = account_id
            cuentas = state.get("cuentas", [])
            account_address = next((c.get("account") for c in cuentas if c.get("id") == account_id), "desconocida")
            state["selected_account_address"] = account_address
            state["step"] = "awaiting_image"
            user_states[user_id] = state
            await safe_answer(f"✅ Cuenta seleccionada: {account_address}")
            await event.edit("📸 **Crear remesa**\n\nAhora envía la **foto** del comprobante:")
        else:
            await safe_answer("⚠️ No estás en el proceso de creación de remesa.", alert=True)
        return

    # ---------- Retiro parcial ----------
    if data == "withdraw_partial:":
        user_states[user_id] = {"action": "withdraw_partial", "step": "awaiting_amount"}
        await event.edit("💰 **Retiro parcial**\n\nEnvía el **monto** que deseas retirar (número positivo):")
        await safe_answer("Ingresa el monto.")
        return

    if data.startswith("withdraw_partial:") and len(data) > len("withdraw_partial:"):
        monto_str = data.split(":", 1)[1]
        try:
            monto = float(monto_str)
            if monto <= 0:
                raise ValueError
        except ValueError:
            await safe_answer("❌ Monto inválido. Debe ser un número positivo.", alert=True)
            return

        usuario = await obtener_usuario_por_telegram_id(user_id)
        if not usuario:
            await safe_answer("No se encontró tu usuario.", alert=True)
            return
        user_uuid = usuario.get("id")
        user_name = usuario.get("name", "Usuario")
        pagos = await listar_pagos()
        saldo_actual = None
        for p in pagos:
            if p.get("userId") == user_uuid:
                saldo_actual = p.get("amount")
                break
        if saldo_actual is None:
            await safe_answer("No se pudo obtener tu saldo.", alert=True)
            return
        if monto > saldo_actual:
            await safe_answer(f"❌ No puedes retirar {monto} porque tu saldo es {saldo_actual}.", alert=True)
            return

        solicitud_id = f"withdraw_{user_id}_{int(asyncio.get_event_loop().time())}"
        user_states[f"pending_{solicitud_id}"] = {
            "user_id": user_id,
            "user_uuid": user_uuid,
            "amount": monto,
            "type": "partial"
        }
        admin_msg = f"💰 *Solicitud de retiro*\n\nUsuario: {user_name} (ID: {user_id})\nMonto: {monto}\nSaldo actual: {saldo_actual}\n\n¿Aprobar?"
        botones_admin = [
            [Button.inline("✅ Confirmar", data=f"approve_withdraw_{solicitud_id}"),
             Button.inline("❌ Rechazar", data=f"reject_withdraw_{solicitud_id}")]
        ]
        try:
            await client.send_message(ADMIN_CHAT_ID, admin_msg, buttons=botones_admin, parse_mode='markdown')
            await event.edit("✅ Solicitud de retiro enviada. Espera confirmación del administrador.")
        except Exception as e:
            logging.error(f"Error al enviar mensaje al administrador: {e}")
            await safe_answer("❌ No se pudo enviar la solicitud al administrador.", alert=True)
        del user_states[user_id]
        await send_user_menu(user_id)
        return

    # ---------- Retiro total ----------
    if data == "withdraw_total:":
        if user_id not in user_states or "current_salary" not in user_states[user_id]:
            await safe_answer("No se pudo obtener tu saldo actual.", alert=True)
            return
        monto = user_states[user_id]["current_salary"]
        if monto <= 0:
            await safe_answer("Tu saldo es 0, no puedes retirar.", alert=True)
            return

        usuario = await obtener_usuario_por_telegram_id(user_id)
        if not usuario:
            await safe_answer("No se encontró tu usuario.", alert=True)
            return
        user_uuid = usuario.get("id")
        user_name = usuario.get("name", "Usuario")
        solicitud_id = f"withdraw_{user_id}_{int(asyncio.get_event_loop().time())}"
        user_states[f"pending_{solicitud_id}"] = {
            "user_id": user_id,
            "user_uuid": user_uuid,
            "amount": monto,
            "type": "total"
        }
        admin_msg = f"💰 *Solicitud de retiro* (total)\n\nUsuario: {user_name} (ID: {user_id})\nMonto: {monto}\nSaldo actual: {monto}\n\n¿Aprobar?"
        botones_admin = [
            [Button.inline("✅ Confirmar", data=f"approve_withdraw_{solicitud_id}"),
             Button.inline("❌ Rechazar", data=f"reject_withdraw_{solicitud_id}")]
        ]
        try:
            await client.send_message(ADMIN_CHAT_ID, admin_msg, buttons=botones_admin, parse_mode='markdown')
            await event.edit("✅ Solicitud de retiro total enviada. Espera confirmación.")
        except Exception as e:
            logging.error(f"Error al enviar mensaje al administrador: {e}")
            await safe_answer("❌ No se pudo enviar la solicitud al administrador.", alert=True)
        del user_states[user_id]
        await send_user_menu(user_id)
        return

    # ---------- Aprobación / rechazo de retiros ----------
    if data.startswith("approve_withdraw_"):
        solicitud_id = data.replace("approve_withdraw_", "")
        es_admin, admin_uuid = await verificar_admin(user_id)
        if not es_admin:
            await safe_answer("⛔ Solo administradores pueden aprobar retiros.", alert=True)
            return
        solicitud = user_states.get(f"pending_{solicitud_id}")
        if not solicitud:
            await safe_answer("❌ Solicitud no encontrada o expirada.", alert=True)
            return
        user_id_solicitante = solicitud["user_id"]
        user_uuid_solicitante = solicitud["user_uuid"]
        amount = solicitud["amount"]
        exito, mensaje = await actualizar_saldo_usuario(user_uuid_solicitante, amount, enabled_sum=False)
        if exito:
            await client.send_message(user_id_solicitante, f"✅ Tu solicitud de retiro por {amount} ha sido CONFIRMADA. El saldo se ha actualizado.")
        else:
            await client.send_message(user_id_solicitante, f"❌ Hubo un error al procesar tu solicitud: {mensaje}")
        await event.edit(f"✅ Retiro aprobado para el usuario {user_id_solicitante} por {amount}.\nResultado: {mensaje}")
        await safe_answer("Retiro aprobado.")
        del user_states[f"pending_{solicitud_id}"]
        await send_admin_menu(user_id)
        return

    if data.startswith("reject_withdraw_"):
        solicitud_id = data.replace("reject_withdraw_", "")
        es_admin, _ = await verificar_admin(user_id)
        if not es_admin:
            await safe_answer("⛔ Solo administradores pueden rechazar retiros.", alert=True)
            return
        solicitud = user_states.get(f"pending_{solicitud_id}")
        if not solicitud:
            await safe_answer("❌ Solicitud no encontrada o expirada.", alert=True)
            return
        user_id_solicitante = solicitud["user_id"]
        amount = solicitud["amount"]
        await client.send_message(user_id_solicitante, f"❌ Tu solicitud de retiro por {amount} ha sido RECHAZADA.")
        await event.edit(f"❌ Retiro rechazado para el usuario {user_id_solicitante} por {amount}.")
        await safe_answer("Retiro rechazado.")
        del user_states[f"pending_{solicitud_id}"]
        await send_admin_menu(user_id)
        return

    # ---------- Eliminación de usuarios ----------
    if data.startswith("confirm_del_"):
        user_uuid = data.replace("confirm_del_", "")
        exito, mensaje = await eliminar_usuario(user_uuid)
        await safe_answer(mensaje, alert=True)
        await event.edit(mensaje)
        await send_admin_menu(user_id)
        return
    if data.startswith("cancel_del"):
        await safe_answer("Eliminación cancelada.")
        await event.edit("❌ Eliminación cancelada.")
        await send_admin_menu(user_id)
        return
    if data.startswith("deluser_"):
        user_uuid = data.replace("deluser_", "")
        botones_confirm = [
            [Button.inline("✅ Sí, eliminar", data=f"confirm_del_{user_uuid}"),
             Button.inline("❌ No, cancelar", data="cancel_del")]
        ]
        await event.edit("⚠️ ¿Seguro que deseas eliminar este usuario?", buttons=botones_confirm)
        await safe_answer("Selecciona una opción.")
        return

    # ---------- Gestión de usuarios ----------
    if data == "createuser":
        es_admin, admin_uuid = await verificar_admin(user_id)
        if es_admin:
            user_states[user_id] = {"action": "create", "step": "awaiting_name", "admin_id": admin_uuid}
            await event.edit("📝 **Crear nuevo usuario**\n\nEnvía el **nombre**:")
            await safe_answer("Ingresa el nombre.")
        else:
            user_states[user_id] = {"action": "request_create", "step": "awaiting_name", "user_telegram_id": user_id}
            await event.edit("📝 **Solicitar creación de usuario**\n\nEnvía tu **nombre**:")
            await safe_answer("Ingresa tu nombre.")
        return

    # Actualizar porcentaje
    if data == "update_percent":
        es_admin, _ = await verificar_admin(user_id)
        if not es_admin:
            await safe_answer("⛔ Solo administradores pueden actualizar porcentajes.", alert=True)
            return
        usuarios = await listar_usuarios()
        if not usuarios:
            await safe_answer("❌ No hay usuarios registrados.", alert=True)
            return
        botones = []
        for u in usuarios[:20]:
            nombre = u.get("name", "Sin nombre")
            uid = u.get("id")
            botones.append([Button.inline(f"📊 {nombre}", data=f"update_percent_user_{uid}")])
        user_states[user_id] = {"action": "select_user_for_percent"}
        await event.edit("Selecciona el usuario para actualizar su porcentaje:", buttons=botones)
        await safe_answer("Selecciona un usuario.")
        return

    if data.startswith("update_percent_user_"):
        user_uuid = data.replace("update_percent_user_", "")
        es_admin, _ = await verificar_admin(user_id)
        if not es_admin:
            await safe_answer("⛔ No eres administrador.", alert=True)
            return
        user_states[user_id] = {"action": "update_percent", "step": "awaiting_percent", "user_uuid": user_uuid}
        await event.edit("💰 Ingresa el **nuevo porcentaje** (número no negativo, ej: 2.5 o 0):")
        await safe_answer("Esperando porcentaje...")
        return

    # Aprobar solicitud de creación de usuario
    if data.startswith("approve_user_"):
        request_id = data.replace("approve_user_", "")
        es_admin, admin_uuid = await verificar_admin(user_id)
        if not es_admin:
            await safe_answer("⛔ Solo administradores pueden aprobar.", alert=True)
            return
        request = user_states.get(f"pending_{request_id}")
        if not request:
            await safe_answer("❌ Solicitud no encontrada o expirada.", alert=True)
            return
        user_states[user_id] = {
            "action": "approving_user",
            "step": "awaiting_percent",
            "name": request["name"],
            "user_telegram_id": request["user_telegram_id"],
            "admin_id": admin_uuid
        }
        del user_states[f"pending_{request_id}"]
        await event.edit("✏️ Ingresa el **porcentaje** para este usuario (número no negativo, ej: 2.5 o 0):")
        await safe_answer("Esperando porcentaje...")
        return

    if data.startswith("reject_user_"):
        request_id = data.replace("reject_user_", "")
        es_admin, _ = await verificar_admin(user_id)
        if not es_admin:
            await safe_answer("⛔ Solo administradores pueden rechazar.", alert=True)
            return
        request = user_states.get(f"pending_{request_id}")
        if request:
            user_id_solicitante = request["user_telegram_id"]
            try:
                await client.send_message(user_id_solicitante, "❌ Tu solicitud de creación de usuario fue rechazada.")
            except:
                pass
            del user_states[f"pending_{request_id}"]
        await event.edit("❌ Solicitud rechazada.")
        await send_admin_menu(user_id)
        return

    # Ver usuarios
    if data == "viewuser":
        es_admin, _ = await verificar_admin(user_id)
        if es_admin:
            usuarios = await listar_usuarios()
            if not usuarios:
                await safe_answer("No hay usuarios.", alert=True)
                return
            mensaje = "📋 **Usuarios:**\n\n"
            for u in usuarios:
                per_cent = u.get('perCent', 0)
                per_cent_str = f"{per_cent:.2f}".rstrip('0').rstrip('.') if isinstance(per_cent, float) else str(per_cent)
                mensaje += (f"**{u.get('name')}** - Telegram ID: `{u.get('idUserTelegram')}` - "
                            f"Porcentaje: {per_cent_str}%\nUUID: `{u.get('id')}`\n\n")
            await event.edit(mensaje)
        else:
            usuario = await obtener_usuario_por_telegram_id(user_id)
            if not usuario:
                await safe_answer("No se encontró tu usuario.", alert=True)
                return
            per_cent = usuario.get('perCent', 0)
            per_cent_str = f"{per_cent:.2f}".rstrip('0').rstrip('.') if isinstance(per_cent, float) else str(per_cent)
            mensaje = f"👤 **Tus datos:**\nNombre: {usuario.get('name')}\nTelegram ID: `{usuario.get('idUserTelegram')}`\nPorcentaje: {per_cent_str}%\nUUID: `{usuario.get('id')}`"
            await event.edit(mensaje)
        await send_user_menu(user_id)
        return

    # Delete user (admin)
    if data == "deleteuser":
        es_admin, _ = await verificar_admin(user_id)
        if not es_admin:
            await safe_answer("⛔ Solo administradores pueden eliminar usuarios.", alert=True)
            return
        usuarios = await listar_usuarios()
        if not usuarios:
            await safe_answer("❌ No hay usuarios.", alert=True)
            return
        botones = []
        for u in usuarios[:20]:
            nombre = u.get("name", "Sin nombre")
            uid = u.get("id")
            botones.append([Button.inline(f"🗑️ {nombre}", data=f"deluser_{uid}")])
        await event.edit("Selecciona el usuario a eliminar:", buttons=botones)
        await safe_answer("Selecciona un usuario.")
        return

    # ---------- Acciones de usuario normal ----------
    if data == "user_create_remesa":
        if user_id in user_states:
            del user_states[user_id]
        usuario = await obtener_usuario_por_telegram_id(user_id)
        if not usuario:
            await safe_answer("❌ No tienes cuenta de usuario.", alert=True)
            return
        user_uuid = usuario.get("id")
        if not user_uuid:
            await safe_answer("❌ UUID inválido.", alert=True)
            return
        user_states[user_id] = {
            "action": "user_create_remesa",
            "step": "awaiting_amount",
            "target_user_uuid": user_uuid
        }
        await event.edit("💸 **Crear remesa**\n\nEnvía el **monto** (número positivo):")
        await safe_answer("Ingresa el monto.")
        return

    if data == "user_view_remesas":
        usuario = await obtener_usuario_por_telegram_id(user_id)
        if not usuario:
            await safe_answer("❌ No tienes cuenta de usuario.", alert=True)
            return
        user_uuid = usuario.get("id")
        if not user_uuid:
            await safe_answer("❌ UUID inválido.", alert=True)
            return
        user_states[user_id] = {"history_user_uuid": user_uuid}
        botones_filtros = [
            [Button.inline("📅 Hoy", data="history_today"),
             Button.inline("📅 7 días", data="history_7d")],
            [Button.inline("📅 30 días", data="history_30d"),
             Button.inline("📅 60 días", data="history_60d")],
            [Button.inline("🔙 Volver", data="history_back"),
             Button.inline("🏠 Volver al menú principal", data="user_back_to_main")]
        ]
        await event.edit("📆 **Selecciona el período para ver tus remesas:**", buttons=botones_filtros)
        await safe_answer("Elige un filtro de fecha.")
        return

    if data == "user_back_to_main":
        await send_user_menu(user_id)
        await event.delete()
        await safe_answer("Volviendo al menú principal.")
        return

    if data.startswith("history_"):
        filtro = data.replace("history_", "")
        state = user_states.get(user_id, {})
        user_uuid = state.get("history_user_uuid")
        if not user_uuid:
            await safe_answer("⚠️ No se encontró tu usuario. Vuelve a intentar con /remesas.", alert=True)
            return

        now = datetime.now(timezone.utc)
        if filtro == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif filtro == "7d":
            start_date = now - timedelta(days=7)
        elif filtro == "30d":
            start_date = now - timedelta(days=30)
        elif filtro == "60d":
            start_date = now - timedelta(days=60)
        elif filtro == "back":
            await send_user_menu(user_id)
            await event.delete()
            return
        else:
            await safe_answer("Filtro no válido.", alert=True)
            return

        history = await listar_history_remittances(user_uuid)
        if history is None:
            await event.edit("❌ Error al obtener el historial de remesas.")
            return

        filtered = []
        for h in history:
            created_at = datetime.fromisoformat(h["createdAt"].replace("Z", "+00:00"))
            if created_at >= start_date:
                filtered.append(h)

        if not filtered:
            await event.edit(f"📭 No hay remesas en el período seleccionado ({filtro}).")
            return

        mensaje = f"📊 **Remesas - {filtro.upper()}**\n\n"
        for idx, h in enumerate(filtered[:20], 1):
            mensaje += (
                f"**{idx}.** Cliente: {h.get('customer', '?')}\n"
                f"   Monto: {h.get('amount')}\n"
                f"   Cuenta: {h.get('account', '?')}\n"
                f"   Salario: {h.get('amountPay')}\n"
                f"   Fecha: {h.get('createdAt')[:10]}\n\n"
            )
        if len(filtered) > 20:
            mensaje += "_Mostrando solo las primeras 20 remesas._"

        botones_volver = [
            [Button.inline("🔙 Volver a filtros", data="user_view_remesas")],
            [Button.inline("🏠 Volver al menú principal", data="user_back_to_main")]
        ]
        await client.send_message(user_id, mensaje, buttons=botones_volver)
        await event.delete()
        await safe_answer("Resultados enviados.")
        return

    if data == "user_view_salary":
        usuario = await obtener_usuario_por_telegram_id(user_id)
        if not usuario:
            await safe_answer("❌ No tienes cuenta de usuario.", alert=True)
            return
        user_uuid = usuario.get("id")
        if not user_uuid:
            await safe_answer("❌ UUID inválido.", alert=True)
            return
        pagos = await listar_pagos()
        if not pagos:
            await safe_answer("No hay registros de pagos.", alert=True)
            await event.edit("📭 No hay salario registrado.")
            return
        mi_pago = None
        for p in pagos:
            if p.get("userId") == user_uuid:
                mi_pago = p
                break
        if not mi_pago:
            await safe_answer("No se encontró tu salario.", alert=True)
            await event.edit("💰 **Tu salario:**\nNo hay información de salario para tu usuario.")
            return
        saldo_actual = mi_pago.get("amount")
        mensaje = f"💰 **Tu salario:**\n\n**Usuario:** {mi_pago.get('userName', '?')}\n**Saldo:** {saldo_actual}\n\nSelecciona una opción:"
        botones = [
            [Button.inline("💰 Retiro parcial", data="withdraw_partial:"),
             Button.inline("💰 Retiro total", data="withdraw_total:"),
             Button.inline("🔙 Cancelar", data="cancel_withdraw")]
        ]
        user_states[user_id] = {"current_salary": saldo_actual, "user_uuid": user_uuid}
        await event.edit(mensaje, buttons=botones)
        await safe_answer("Selecciona una opción.")
        return

    if data == "cancel_withdraw":
        if user_id in user_states:
            del user_states[user_id]
        usuario = await obtener_usuario_por_telegram_id(user_id)
        if not usuario:
            await event.edit("❌ No tienes cuenta de usuario.")
            return
        user_uuid = usuario.get("id")
        user_states[user_id] = {"user_uuid": user_uuid}
        await send_user_menu(user_id)
        await event.delete()
        return

    # ---------- Acciones de administrador (remesas) ----------
    if data == "admin_view_remesas":
        es_admin, _ = await verificar_admin(user_id)
        if not es_admin:
            await safe_answer("⛔ No eres administrador.", alert=True)
            return
        user_states[user_id] = {"action": "admin_history_filters"}
        botones_filtros = [
            [Button.inline("📅 Hoy", data="admin_history_today"),
             Button.inline("📅 7 días", data="admin_history_7d")],
            [Button.inline("📅 30 días", data="admin_history_30d"),
             Button.inline("📅 60 días", data="admin_history_60d")],
            [Button.inline("🔙 Volver al menú", data="admin_history_back")]
        ]
        await event.edit("📆 **Selecciona el período para ver el historial de remesas:**", buttons=botones_filtros)
        await safe_answer("Elige un filtro de fecha.")
        return

    if data.startswith("admin_history_"):
        filtro = data.replace("admin_history_", "")
        if filtro == "back":
            botones = [
                [Button.inline("➕ Crear remesa", data="admin_create_remesa"),
                 Button.inline("✏️ Actualizar remesa", data="admin_update_remesa")],
                [Button.inline("👁️ Ver remesas", data="admin_view_remesas"),
                 Button.inline("💰 Ver salario", data="admin_view_salary")]
            ]
            await event.edit("📦 **Gestión de remesas y salarios**\nSelecciona una acción:", buttons=botones)
            await safe_answer("Volviendo al menú.")
            return

        es_admin, _ = await verificar_admin(user_id)
        if not es_admin:
            await safe_answer("⛔ No eres administrador.", alert=True)
            return

        # Guardar el filtro seleccionado
        user_states[user_id] = {"admin_selected_filter": filtro}
        # Eliminar mensaje de filtros
        await event.delete()
        # Obtener usuarios
        usuarios = await listar_usuarios()
        if not usuarios:
            await client.send_message(
                user_id,
                "❌ No hay usuarios registrados o no se pudo obtener la lista.\n\nUsa /user para crear un usuario.",
                buttons=[[Button.inline("🔙 Volver al menú", data="admin_back_to_menu")]]
            )
            await safe_answer("Error: lista de usuarios vacía.")
            return

        # Construir botones de usuarios
        botones_usuarios = []
        for u in usuarios[:20]:
            nombre = u.get("name", "Sin nombre")
            uid = u.get("id")
            botones_usuarios.append([Button.inline(f"👤 {nombre}", data=f"admin_history_user_{uid}")])
        # Botón para volver a filtros
        botones_usuarios.append([Button.inline("🔙 Volver a filtros", data="admin_view_remesas")])

        await client.send_message(
            user_id,
            f"📌 **Selecciona un usuario para ver sus remesas en el período: {filtro.upper()}**",
            buttons=botones_usuarios
        )
        await safe_answer("Selecciona un usuario.")
        return

    if data.startswith("admin_history_user_"):
        user_uuid = data.replace("admin_history_user_", "")
        es_admin, _ = await verificar_admin(user_id)
        if not es_admin:
            await safe_answer("⛔ No eres administrador.", alert=True)
            return
        state = user_states.get(user_id, {})
        filtro = state.get("admin_selected_filter")
        if not filtro:
            await safe_answer("❌ No se ha seleccionado un filtro de fecha. Vuelve a empezar.", alert=True)
            await client.send_message(user_id, "Por favor, selecciona un período desde /remesas -> Ver remesas.")
            return

        now = datetime.now(timezone.utc)
        if filtro == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif filtro == "7d":
            start_date = now - timedelta(days=7)
        elif filtro == "30d":
            start_date = now - timedelta(days=30)
        elif filtro == "60d":
            start_date = now - timedelta(days=60)
        else:
            await safe_answer("Filtro no válido.", alert=True)
            return

        history = await listar_history_remittances(user_uuid)
        if history is None:
            await client.send_message(
                user_id,
                "❌ Error al obtener el historial de remesas para este usuario.",
                buttons=[[Button.inline("🔙 Volver a selección de usuario", data="admin_view_remesas")]]
            )
            return

        filtered = []
        for h in history:
            created_at = datetime.fromisoformat(h["createdAt"].replace("Z", "+00:00"))
            if created_at >= start_date:
                filtered.append(h)

        if not filtered:
            await client.send_message(
                user_id,
                f"📭 No hay remesas para este usuario en el período seleccionado ({filtro}).",
                buttons=[[Button.inline("🔙 Volver a selección de usuario", data="admin_view_remesas")]]
            )
            await event.delete()
            return

        filtered.sort(key=lambda x: x["createdAt"], reverse=True)
        mensaje = f"📊 **Remesas del usuario - {filtro.upper()}**\n\n"
        for idx, h in enumerate(filtered[:30], 1):
            mensaje += (
                f"**{idx}.** Cliente: {h.get('customer', '?')}\n"
                f"   Monto: {h.get('amount')}\n"
                f"   Cuenta: {h.get('account', '?')}\n"
                f"   Salario: {h.get('amountPay')}\n"
                f"   Fecha: {h.get('createdAt')[:10]}\n\n"
            )
        if len(filtered) > 30:
            mensaje += "_Mostrando solo las primeras 30 remesas._"

        botones_volver = [
            [Button.inline("🔙 Volver a selección de usuario", data="admin_view_remesas")],
            [Button.inline("🏠 Volver al menú principal", data="admin_back_to_menu")]
        ]
        await client.send_message(user_id, mensaje, buttons=botones_volver)
        await event.delete()
        await safe_answer("Resultados enviados.")
        return

    if data == "admin_back_to_menu":
        await send_admin_menu(user_id)
        await event.delete()
        await safe_answer("Volviendo al menú principal.")
        return

    if data == "admin_view_salary":
        pagos = await listar_pagos()
        if not pagos:
            await safe_answer("No hay registros de pagos.", alert=True)
            await event.edit("📭 No hay salarios registrados.")
            return
        mensaje = "💰 **Lista de salarios:**\n\n"
        for p in pagos:
            mensaje += (f"**Usuario:** {p.get('userName', '?')}\n"
                        f"**Saldo:** {p.get('amount')}\n"
                        f"**User ID:** `{p.get('userId', '?')}`\n\n")
        if len(mensaje) > 4000:
            for i in range(0, len(mensaje), 4000):
                await event.reply(mensaje[i:i+4000])
        else:
            await event.reply(mensaje)
        await event.delete()
        await safe_answer("Lista de salarios mostrada.")
        await send_admin_menu(user_id)
        return

    if data == "admin_create_remesa":
        usuarios = await listar_usuarios()
        if not usuarios:
            await safe_answer("❌ No hay usuarios registrados. Crea un usuario primero.", alert=True)
            return
        botones_usuarios = []
        for u in usuarios[:20]:
            nombre = u.get("name", "Sin nombre")
            uid = u.get("id")
            botones_usuarios.append([Button.inline(f"👤 {nombre}", data=f"create_remesa_user_{uid}")])
        user_states[user_id] = {"action": "admin_create_remesa", "step": "select_user"}
        await event.edit("Selecciona el usuario para la nueva remesa:", buttons=botones_usuarios)
        await safe_answer("Selecciona un usuario.")
        return

    if data.startswith("create_remesa_user_"):
        user_uuid = data.replace("create_remesa_user_", "")
        user_states[user_id] = {
            "action": "admin_create_remesa",
            "step": "awaiting_amount",
            "target_user_uuid": user_uuid
        }
        await event.edit("💸 **Crear remesa**\n\nEnvía el **monto** (número positivo):")
        await safe_answer("Ingresa el monto.")
        return

    if data == "admin_update_remesa":
        remesas = await listar_remesas()
        if not remesas:
            await safe_answer("❌ No hay remesas para actualizar.", alert=True)
            await event.edit("📭 No hay remesas.")
            return
        remesas_pendientes = [r for r in remesas if r.get("enabled") is False]
        if not remesas_pendientes:
            await safe_answer("No hay remesas pendientes de confirmar.", alert=True)
            await event.edit("📭 No hay remesas pendientes.")
            return
        await event.edit("🔄 Mostrando todas las remesas pendientes de confirmar...")
        for remesa in remesas_pendientes:
            remesa_id = remesa.get("id")
            texto_detalles = (
                f"📄 **Detalles de la remesa**\n\n"
                f"**ID:** `{remesa_id}`\n"
                f"**Usuario:** {remesa.get('userName', '?')}\n"
                f"**Cliente:** {remesa.get('customer', '?')}\n"
                f"**Monto:** {remesa.get('amount')}\n"
                f"**Cuenta:** {remesa.get('address', '?')}\n"
                f"**Habilitada:** ❌\n"
            )
            img_path = remesa.get('urlImage', '')
            botones_acciones = [
                Button.inline("✅ Confirmar remesa", data=f"confirm_update_remesa_{remesa_id}"),
                Button.inline("❌ Remesa no confirmada", data=f"delete_remesa_{remesa_id}")
            ]
            try:
                if img_path and img_path != "string" and os.path.exists(img_path):
                    await client.send_file(event.chat_id, img_path, caption=texto_detalles, buttons=[botones_acciones])
                else:
                    await client.send_message(event.chat_id, texto_detalles, buttons=[botones_acciones])
            except Exception as e:
                logging.error(f"Error al enviar remesa {remesa_id}: {e}")
                await client.send_message(event.chat_id, f"❌ Error al mostrar remesa {remesa_id}")
        await safe_answer("Remesas pendientes mostradas.")
        return

    if data.startswith("confirm_update_remesa_"):
        remesa_id = data.replace("confirm_update_remesa_", "")
        es_admin, admin_uuid = await verificar_admin(user_id)
        if not es_admin:
            await safe_answer("⛔ No eres administrador.", alert=True)
            return

        remesas = await listar_remesas()
        remesa = None
        for r in remesas:
            if r.get("id") == remesa_id:
                remesa = r
                break
        if not remesa:
            await safe_answer("❌ Remesa no encontrada.", alert=True)
            return

        current_user_id = remesa.get("userId")
        current_amount = remesa.get("amount")
        current_url_image = remesa.get("urlImage")
        account_address = remesa.get("address", "")
        customer = remesa.get("customer", "")
        account_id_remesa = remesa.get("accountId")

        exito, mensaje = await confirmar_remesa(remesa_id, admin_uuid)

        if exito:
            if current_user_id:
                usuario_destino = await obtener_usuario_por_uuid(current_user_id)
                if usuario_destino:
                    telegram_id_destino = usuario_destino.get("idUserTelegram")
                    if telegram_id_destino:
                        try:
                            destinatario = await client.get_entity(telegram_id_destino)
                            if current_url_image and current_url_image != "string" and os.path.exists(current_url_image):
                                await client.send_file(destinatario, current_url_image, caption="✅ Remesa confirmada")
                            else:
                                await client.send_message(destinatario, "✅ Remesa confirmada")
                        except Exception as e:
                            logging.error(f"Error al notificar: {e}")
                            mensaje += f"\n⚠️ Error al notificar: {str(e)}"
                    else:
                        mensaje += "\n⚠️ El usuario no tiene Telegram ID definido."
                else:
                    mensaje += f"\n⚠️ No se encontró usuario con UUID {current_user_id}."

            if current_user_id:
                exito_saldo, msg_saldo = await actualizar_saldo_usuario(current_user_id, current_amount, enabled_sum=True)
                mensaje += f"\n{msg_saldo}"
            else:
                mensaje += "\n⚠️ La remesa no tiene userId, no se actualizó saldo."

            if not account_id_remesa and account_address:
                cuentas = await listar_cuentas()
                for c in cuentas:
                    if c.get("account") == account_address:
                        account_id_remesa = c.get("id")
                        break
            if account_id_remesa:
                exito_cuenta, msg_cuenta = await actualizar_balance_cuenta(account_id_remesa, admin_uuid, current_amount)
                mensaje += f"\n{msg_cuenta}"
            else:
                mensaje += "\n⚠️ No se encontró la cuenta asociada a esta remesa. No se actualizó el balance de cuenta."

            if current_user_id and account_address:
                exito_history, msg_history = await crear_history_remittance(
                    user_id=current_user_id,
                    account=account_address,
                    amount=current_amount,
                    customer=customer
                )
                mensaje += f"\n{msg_history}"
            else:
                mensaje += "\n⚠️ No se pudo registrar el historial (falta userId o cuenta)."

        await event.edit(mensaje)
        await safe_answer("Remesa actualizada.", alert=True)
        await send_admin_menu(user_id)
        return

    if data.startswith("delete_remesa_"):
        remesa_id = data.replace("delete_remesa_", "")
        es_admin, admin_uuid = await verificar_admin(user_id)
        if not es_admin:
            await safe_answer("⛔ No eres administrador.", alert=True)
            return
        remesas = await listar_remesas()
        remesa = None
        for r in remesas:
            if r.get("id") == remesa_id:
                remesa = r
                break
        if not remesa:
            await safe_answer("❌ Remesa no encontrada.", alert=True)
            return

        current_user_id = remesa.get("userId")
        current_url_image = remesa.get("urlImage")
        notificacion_msg = ""

        if current_user_id:
            usuario_destino = await obtener_usuario_por_uuid(current_user_id)
            if usuario_destino:
                telegram_id_destino = usuario_destino.get("idUserTelegram")
                if telegram_id_destino:
                    try:
                        destinatario = await client.get_entity(telegram_id_destino)
                        if current_url_image and current_url_image != "string" and os.path.exists(current_url_image):
                            await client.send_file(
                                destinatario,
                                current_url_image,
                                caption="❌ Remesa no confirmada. Por favor, contacte al cliente y vuelva a crearla cuando realice el pago."
                            )
                        else:
                            await client.send_message(
                                destinatario,
                                "❌ Remesa no confirmada. Por favor, contacte al cliente y vuelva a crearla cuando realice el pago."
                            )
                        notificacion_msg = "\n✅ Se notificó al usuario."
                    except Exception as e:
                        logging.error(f"Error al notificar eliminación: {e}")
                        notificacion_msg = f"\n⚠️ Error al notificar al usuario: {str(e)}"
                else:
                    notificacion_msg = "\n⚠️ El usuario no tiene Telegram ID definido."
            else:
                notificacion_msg = f"\n⚠️ No se encontró usuario con UUID {current_user_id}."

        if current_url_image and current_url_image != "string" and os.path.exists(current_url_image):
            await eliminar_archivo_imagen(current_url_image)
            notificacion_msg += "\n✅ Imagen eliminada localmente."

        exito, msg_eliminar = await eliminar_remesa(remesa_id)
        if exito:
            resultado = f"✅ Remesa eliminada correctamente.{notificacion_msg}\n{msg_eliminar}"
        else:
            resultado = f"❌ Error al eliminar remesa: {msg_eliminar}{notificacion_msg}"

        await event.edit(resultado)
        await safe_answer("Remesa eliminada.", alert=True)
        await send_admin_menu(user_id)
        return

    # ---------- Acciones de administrador (cuentas) ----------
    if data == "admin_create_account":
        es_admin, admin_uuid = await verificar_admin(user_id)
        if not es_admin:
            await safe_answer("⛔ No eres administrador.", alert=True)
            return
        user_states[user_id] = {"action": "create_account", "step": "awaiting_account", "admin_id": admin_uuid}
        await event.edit("🏦 **Crear cuenta**\n\nEnvía la **dirección de la cuenta**:")
        await safe_answer("Ingresa la dirección de la cuenta.")
        return

    if data == "admin_withdraw":
        cuentas = await listar_cuentas()
        if not cuentas:
            await safe_answer("❌ No hay cuentas registradas.", alert=True)
            await event.edit("📭 No hay cuentas disponibles.")
            return
        user_states[user_id] = {"action": "withdraw", "step": "select_account", "cuentas": cuentas}
        botones_cuentas = []
        for c in cuentas[:20]:
            account_num = c.get("account", "?")
            account_id = c.get("id")
            botones_cuentas.append([Button.inline(f"🏦 {account_num}", data=f"withdraw_account_{account_id}")])
        await event.edit("Selecciona la cuenta de la que deseas retirar saldo:", buttons=botones_cuentas)
        await safe_answer("Selecciona una cuenta.")
        return

    if data.startswith("withdraw_account_"):
        account_id = data.replace("withdraw_account_", "")
        es_admin, admin_uuid = await verificar_admin(user_id)
        if not es_admin:
            await safe_answer("⛔ No eres administrador.", alert=True)
            return
        user_states[user_id] = {
            "action": "withdraw",
            "step": "awaiting_value",
            "account_id": account_id,
            "admin_id": admin_uuid
        }
        await event.edit("💸 **Retirar saldo**\n\nEnvía el **monto** a retirar (número positivo):")
        await safe_answer("Ingresa el monto.")
        return

    if data == "admin_view_accounts":
        cuentas = await listar_cuentas()
        if not cuentas:
            await safe_answer("No hay cuentas registradas.", alert=True)
            await event.edit("📭 No hay cuentas.")
            return
        await mostrar_cuentas(event, cuentas, titulo="🏦 **Lista de cuentas:**")
        await event.delete()
        await send_admin_menu(user_id)
        return

# --------------------------------------------------------------
# Conversación (mensajes de texto)
# --------------------------------------------------------------
@client.on(events.NewMessage)
async def conversation_handler(event):
    user_id = event.sender_id
    if user_id not in user_states:
        return
    state = user_states[user_id]
    if "action" not in state:
        del user_states[user_id]
        return
    action = state["action"]
    text = event.raw_text.strip()
    if text.lower() == "cancel":
        del user_states[user_id]
        es_admin, _ = await verificar_admin(user_id)
        if es_admin:
            await send_admin_menu(user_id)
        else:
            await send_user_menu(user_id)
        await event.reply("❌ Operación cancelada.")
        return

    # Creación de usuario por admin
    if action == "create":
        if state["step"] == "awaiting_name":
            state["name"] = text
            state["step"] = "awaiting_telegram_id"
            user_states[user_id] = state
            await event.reply("✅ Nombre guardado.\n\nEnvía el **ID de Telegram** del nuevo usuario (número):")
        elif state["step"] == "awaiting_telegram_id":
            try:
                telegram_id = int(text)
            except ValueError:
                await event.reply("❌ Debe ser un número entero. Intenta de nuevo:")
                return
            state["id_user_telegram"] = telegram_id
            state["step"] = "awaiting_percent"
            user_states[user_id] = state
            await event.reply("✅ ID de Telegram guardado.\n\nEnvía el **porcentaje** (número no negativo, ej: 2.5 o 0):")
        elif state["step"] == "awaiting_percent":
            try:
                per_cent = float(text)
                if per_cent < 0:
                    raise ValueError
            except ValueError:
                await event.reply("❌ Debe ser un número no negativo (puede ser decimal). Intenta de nuevo:")
                return
            name = state["name"]
            telegram_id = state["id_user_telegram"]
            admin_id = state["admin_id"]
            exito, mensaje, user_uuid = await crear_usuario(name, telegram_id, admin_id, per_cent)
            if exito and user_uuid:
                pago_exito, pago_mensaje = await crear_pay(user_uuid)
                respuesta = f"{mensaje}\n{pago_mensaje}\nPorcentaje asignado: {per_cent}%"
            else:
                respuesta = mensaje
            await event.reply(respuesta)
            del user_states[user_id]
            await send_admin_menu(user_id)
            return

    # Solicitud de creación por usuario normal
    elif action == "request_create":
        if state["step"] == "awaiting_name":
            name = text
            request_id = f"user_request_{user_id}_{int(asyncio.get_event_loop().time())}"
            user_states[f"pending_{request_id}"] = {
                "type": "user_creation",
                "user_telegram_id": user_id,
                "name": name
            }
            admin_msg = f"👤 *Solicitud de nuevo usuario*\n\nNombre: {name}\nTelegram ID: `{user_id}`\n\n¿Aprobar?"
            botones_admin = [
                [Button.inline("✅ Aprobar", data=f"approve_user_{request_id}"),
                 Button.inline("❌ Rechazar", data=f"reject_user_{request_id}")]
            ]
            try:
                await client.send_message(ADMIN_CHAT_ID, admin_msg, buttons=botones_admin, parse_mode='markdown')
                await event.reply("✅ Solicitud enviada al administrador. Espera la aprobación.")
            except Exception as e:
                logging.error(f"Error al enviar solicitud: {e}")
                await event.reply("❌ Error al enviar la solicitud. Intenta más tarde.")
            del user_states[user_id]
            await send_user_menu(user_id)
            return

    # Admin aprobando y pidiendo porcentaje
    elif action == "approving_user":
        if state["step"] == "awaiting_percent":
            try:
                per_cent = float(text)
                if per_cent < 0:
                    raise ValueError
            except ValueError:
                await event.reply("❌ Debe ser un número no negativo (puede ser decimal). Intenta de nuevo:")
                return
            name = state["name"]
            user_telegram_id = state["user_telegram_id"]
            admin_id = state["admin_id"]
            exito, mensaje, user_uuid = await crear_usuario(name, user_telegram_id, admin_id, per_cent)
            if exito and user_uuid:
                pago_exito, pago_mensaje = await crear_pay(user_uuid)
                respuesta = f"{mensaje}\n{pago_mensaje}\nPorcentaje asignado: {per_cent}%"
                try:
                    await client.send_message(user_telegram_id, f"✅ Tu usuario ha sido creado con nombre '{name}'. Ahora puedes usar el bot.")
                except:
                    pass
            else:
                respuesta = mensaje
            await event.reply(respuesta)
            del user_states[user_id]
            await send_admin_menu(user_id)
            return

    # Admin actualizando porcentaje
    elif action == "update_percent":
        if state["step"] == "awaiting_percent":
            try:
                new_percent = float(text)
                if new_percent < 0:
                    raise ValueError
            except ValueError:
                await event.reply("❌ Debe ser un número no negativo (puede ser decimal). Intenta de nuevo:")
                return
            user_uuid = state["user_uuid"]
            usuario = await obtener_usuario_por_uuid(user_uuid)
            if not usuario:
                await event.reply("❌ Usuario no encontrado.")
                del user_states[user_id]
                await send_admin_menu(user_id)
                return
            exito, mensaje = await actualizar_usuario(user_uuid, usuario["name"], usuario["idUserTelegram"], new_percent)
            await event.reply(mensaje)
            del user_states[user_id]
            await send_admin_menu(user_id)
            return

    # Admin creando remesa
    elif action == "admin_create_remesa":
        if state["step"] == "awaiting_amount":
            try:
                amount = float(text)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                await event.reply("❌ Monto inválido. Envía un número positivo (ej: 150.00):")
                return
            state["amount"] = amount
            state["step"] = "awaiting_customer"
            user_states[user_id] = state
            await event.reply("✅ Monto guardado.\n\nEnvía el **nombre del cliente** destinatario:")
        elif state["step"] == "awaiting_customer":
            state["customer"] = text
            state["step"] = "awaiting_account_selection"
            user_states[user_id] = state
            cuentas = await listar_cuentas()
            if not cuentas:
                await event.reply("❌ No hay cuentas registradas. Crea una cuenta primero usando /cuentas.")
                del user_states[user_id]
                await send_admin_menu(user_id)
                return
            botones_cuentas = []
            for idx, c in enumerate(cuentas[:20], start=1):
                account_address = c.get("account", "?")
                account_id = c.get("id")
                botones_cuentas.append([Button.inline(f"{idx} - {account_address}", data=f"select_account_{account_id}")])
            await event.reply("🏦 **Selecciona la cuenta destino:**", buttons=botones_cuentas)
            state["cuentas"] = cuentas
            user_states[user_id] = state
        elif state["step"] == "awaiting_image":
            if not event.message.photo:
                await event.reply("❌ Debes enviar una foto. Intenta de nuevo:")
                return
            ruta_imagen = await descargar_imagen(event.message, user_id)
            if not ruta_imagen:
                await event.reply("❌ No se pudo guardar la imagen.")
                return
            exito, mensaje = await crear_remesa(
                user_id=state["target_user_uuid"],
                amount=state["amount"],
                customer=state["customer"],
                url_image=ruta_imagen,
                account_id=state["selected_account_id"]
            )
            await event.reply(mensaje)
            del user_states[user_id]
            await send_admin_menu(user_id)
            return

    # Usuario normal creando remesa
    elif action == "user_create_remesa":
        if state["step"] == "awaiting_amount":
            try:
                amount = float(text)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                await event.reply("❌ Monto inválido. Envía un número positivo (ej: 150.00):")
                return
            state["amount"] = amount
            state["step"] = "awaiting_customer"
            user_states[user_id] = state
            await event.reply("✅ Monto guardado.\n\nEnvía el **nombre del cliente** destinatario:")
        elif state["step"] == "awaiting_customer":
            state["customer"] = text
            state["step"] = "awaiting_account_selection"
            user_states[user_id] = state
            cuentas = await listar_cuentas()
            if not cuentas:
                await event.reply("❌ No hay cuentas registradas. Contacta a un administrador.")
                del user_states[user_id]
                await send_user_menu(user_id)
                return
            botones_cuentas = []
            for idx, c in enumerate(cuentas[:20], start=1):
                account_address = c.get("account", "?")
                account_id = c.get("id")
                botones_cuentas.append([Button.inline(f"{idx} - {account_address}", data=f"select_account_{account_id}")])
            await event.reply("🏦 **Selecciona la cuenta destino:**", buttons=botones_cuentas)
            state["cuentas"] = cuentas
            user_states[user_id] = state
        elif state["step"] == "awaiting_image":
            if not event.message.photo:
                await event.reply("❌ Debes enviar una foto. Intenta de nuevo:")
                return
            ruta_imagen = await descargar_imagen(event.message, user_id)
            if not ruta_imagen:
                await event.reply("❌ No se pudo guardar la imagen.")
                return
            exito, mensaje = await crear_remesa(
                user_id=state["target_user_uuid"],
                amount=state["amount"],
                customer=state["customer"],
                url_image=ruta_imagen,
                account_id=state["selected_account_id"]
            )
            await event.reply(mensaje)
            del user_states[user_id]
            await send_user_menu(user_id)
            return

    # Retiro parcial (flujo iniciado por usuario) – ya manejado en callbacks
    elif action == "withdraw_partial":
        # Este bloque normalmente no se usa porque se maneja en el callback, pero por seguridad:
        if state["step"] == "awaiting_amount":
            try:
                monto = float(text)
                if monto <= 0:
                    raise ValueError
            except ValueError:
                await event.reply("❌ Monto inválido. Envía un número positivo (ej: 100.00):")
                return
            usuario = await obtener_usuario_por_telegram_id(user_id)
            if not usuario:
                await event.reply("No se encontró tu usuario.")
                del user_states[user_id]
                return
            user_uuid = usuario.get("id")
            user_name = usuario.get("name", "Usuario")
            pagos = await listar_pagos()
            saldo_actual = None
            for p in pagos:
                if p.get("userId") == user_uuid:
                    saldo_actual = p.get("amount")
                    break
            if saldo_actual is None:
                await event.reply("No se pudo obtener tu saldo.")
                del user_states[user_id]
                return
            if monto > saldo_actual:
                await event.reply(f"❌ No puedes retirar {monto} porque tu saldo es {saldo_actual}.")
                return

            solicitud_id = f"withdraw_{user_id}_{int(asyncio.get_event_loop().time())}"
            user_states[f"pending_{solicitud_id}"] = {
                "user_id": user_id,
                "user_uuid": user_uuid,
                "amount": monto,
                "type": "partial"
            }
            admin_msg = f"💰 *Solicitud de retiro*\n\nUsuario: {user_name} (ID: {user_id})\nMonto: {monto}\nSaldo actual: {saldo_actual}\n\n¿Aprobar?"
            botones_admin = [
                [Button.inline("✅ Confirmar", data=f"approve_withdraw_{solicitud_id}"),
                 Button.inline("❌ Rechazar", data=f"reject_withdraw_{solicitud_id}")]
            ]
            try:
                await client.send_message(ADMIN_CHAT_ID, admin_msg, buttons=botones_admin, parse_mode='markdown')
                await event.reply("✅ Solicitud de retiro enviada al administrador. Espera la confirmación.")
            except Exception as e:
                logging.error(f"Error al enviar mensaje al administrador: {e}")
                await event.reply("❌ No se pudo enviar la solicitud al administrador.")
            del user_states[user_id]
            return

    # Crear cuenta (admin)
    elif action == "create_account":
        if state["step"] == "awaiting_account":
            account_address = text
            admin_id = state["admin_id"]
            exito, mensaje = await crear_cuenta(account_address, admin_id)
            await event.reply(mensaje)
            del user_states[user_id]
            await send_admin_menu(user_id)
            return

    # Retirar saldo de cuenta (admin)
    elif action == "withdraw":
        if state["step"] == "awaiting_value":
            try:
                value = float(text)
                if value <= 0:
                    raise ValueError
            except ValueError:
                await event.reply("❌ Monto inválido. Envía un número positivo (ej: 100.00):")
                return
            account_id = state["account_id"]
            admin_id = state["admin_id"]
            exito, mensaje = await retirar_saldo(account_id, admin_id, value)
            await event.reply(mensaje)
            del user_states[user_id]
            await send_admin_menu(user_id)
            return

# --------------------------------------------------------------
# Tarea en segundo plano: reporte diario a las 20:00 Cuba (UTC 0)
# --------------------------------------------------------------
async def daily_report_task():
    while True:
        now = datetime.now(timezone.utc)
        target_hour = 0  # 20:00 Cuba = 00:00 UTC
        target_minute = 0
        target_second = 0
        next_run = now.replace(hour=target_hour, minute=target_minute, second=target_second, microsecond=0)
        if now >= next_run:
            next_run += timedelta(days=1)
        sleep_seconds = (next_run - now).total_seconds()
        logging.info(f"Próximo reporte diario en {sleep_seconds/3600:.2f} horas (a las {target_hour:02d}:{target_minute:02d} UTC)")
        await asyncio.sleep(sleep_seconds)

        logging.info("Ejecutando reporte diario de remesas...")
        try:
            usuarios = await listar_usuarios()
            if not usuarios:
                logging.error("No se pudo obtener la lista de usuarios para el reporte diario.")
                continue

            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

            for user_data in usuarios:
                user_uuid = user_data.get("id")
                user_telegram_id = user_data.get("idUserTelegram")
                user_name = user_data.get("name", "Usuario")
                if not user_uuid or not user_telegram_id:
                    logging.warning(f"Usuario {user_name} sin UUID o Telegram ID, se omite.")
                    continue

                history = await listar_history_remittances(user_uuid)
                if not history:
                    continue

                today_remittances = []
                for h in history:
                    created_at = datetime.fromisoformat(h["createdAt"].replace("Z", "+00:00"))
                    if created_at >= today_start:
                        today_remittances.append(h)

                if not today_remittances:
                    continue

                lines = [f"📊 *Reporte de remesas del día*", f"Usuario: {user_name}", ""]
                for idx, r in enumerate(today_remittances, 1):
                    lines.append(
                        f"*{idx}.* Cliente: {r.get('customer', '?')}\n"
                        f"   Monto: {r.get('amount')}\n"
                        f"   Cuenta: {r.get('account', '?')}\n"
                        f"   Salario: {r.get('amountPay')}"
                    )
                message = "\n".join(lines)

                try:
                    await client.send_message(int(user_telegram_id), message, parse_mode='markdown')
                    logging.info(f"Reporte enviado a {user_name} (ID: {user_telegram_id})")
                except Exception as e:
                    logging.error(f"Error al enviar reporte a {user_name} ({user_telegram_id}): {e}")

        except Exception as e:
            logging.error(f"Error en la tarea de reporte diario: {e}", exc_info=True)

# --------------------------------------------------------------
# Inicio del bot
# --------------------------------------------------------------
async def main():
    await client.start(bot_token=BOT_TOKEN)
    logging.info("✅ Bot iniciado correctamente")
    asyncio.create_task(daily_report_task())
    await client.run_until_disconnected()

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logging.info("Bot detenido por el usuario")
    finally:
        loop.close()