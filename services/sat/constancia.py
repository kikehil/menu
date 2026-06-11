import os
import asyncio
from datetime import datetime
import nodriver as uc
from config import DOCUMENTS_PATH, SAT_EFIRMA_CER_PATH, SAT_EFIRMA_KEY_PATH, SAT_EFIRMA_PASSWORD, SAT_RFC

LOGIN_URL = "https://wwwmat.sat.gob.mx/personas/iniciar-sesion"
CONSTANCIA_URL = "https://wwwmat.sat.gob.mx/aplicacion/operacion/66862/constancia-de-situacion-fiscal"


async def _snap(page, name):
    path = os.path.abspath(f"{DOCUMENTS_PATH}/debug_{name}.png")
    await page.save_screenshot(path)
    print(f"[DEBUG] snap → {path}")


async def descargar_constancia() -> str:
    os.makedirs(DOCUMENTS_PATH, exist_ok=True)
    fecha = datetime.now().strftime("%Y-%m")
    destino = os.path.abspath(f"{DOCUMENTS_PATH}/constancia_{fecha}.pdf")

    browser = await uc.start(headless=False, lang="es-MX")
    try:
        page = await browser.get(LOGIN_URL)
        # Esperar a que el formulario esté visible
        await page.find("Acceso por contraseña", timeout=30)
        await asyncio.sleep(2)
        await _snap(page, "01_login")
        print(f"[DEBUG] URL inicial: {page.url}")

        # Obtener todos los botones y mostrar su texto para debug
        all_btns = await page.select_all("button")
        print(f"[DEBUG] Total botones: {len(all_btns)}")
        for i, b in enumerate(all_btns):
            txt = await b.get_attribute("textContent") or ""
            val = await b.get_attribute("value") or ""
            print(f"[DEBUG]  btn[{i}] textContent={txt.strip()!r} value={val!r}")

        # Clic en el primer botón que no sea "Enviar" (debe ser "e.firma")
        for b in all_btns:
            txt = (await b.get_attribute("textContent") or "").strip()
            if txt and "enviar" not in txt.lower() and "contraseña" not in txt.lower():
                await b.click()
                print(f"[DEBUG] Clic en botón: {txt!r}")
                break

        # Esperar a que cargue el formulario de e.firma
        await page.find("Certificado", timeout=20)
        await asyncio.sleep(2)
        await _snap(page, "02_efirma_form")
        print("[DEBUG] Formulario e.firma cargado")

        # Listar todos los inputs visibles para debug
        all_inputs = await page.select_all("input")
        print(f"[DEBUG] Total inputs en formulario: {len(all_inputs)}")
        for i, inp in enumerate(all_inputs):
            t = await inp.get_attribute("type") or "text"
            ph = await inp.get_attribute("placeholder") or ""
            print(f"[DEBUG]   input[{i}] type={t!r} placeholder={ph!r}")

        # Llenar campos de texto con las rutas
        for inp in all_inputs:
            try:
                ph = (await inp.get_attribute("placeholder") or "").lower()
                t = (await inp.get_attribute("type") or "text").lower()
            except Exception:
                continue
            if "certificado" in ph or "cer" in ph:
                await inp.send_keys(SAT_EFIRMA_CER_PATH)
                print(f"[DEBUG] .cer → {SAT_EFIRMA_CER_PATH}")
            elif "llave" in ph or "key" in ph or "privada" in ph:
                await inp.send_keys(SAT_EFIRMA_KEY_PATH)
                print(f"[DEBUG] .key → {SAT_EFIRMA_KEY_PATH}")
            elif t == "password":
                await inp.send_keys(SAT_EFIRMA_PASSWORD)
                print("[DEBUG] password ingresada")
            elif "rfc" in ph.lower():
                await inp.send_keys(SAT_RFC)
                print(f"[DEBUG] RFC → {SAT_RFC}")

        await asyncio.sleep(1)
        await _snap(page, "03_filled")

        # Clic en Enviar
        enviar = await page.find("Enviar", best_match=True, timeout=10)
        await enviar.click()
        await asyncio.sleep(6)
        print(f"[DEBUG] Post-login URL: {page.url}")
        await _snap(page, "04_post_login")

        # Navegar a constancia
        page = await browser.get(CONSTANCIA_URL)
        await asyncio.sleep(5)
        await _snap(page, "05_constancia")
        print(f"[DEBUG] Constancia URL: {page.url}")

        # Buscar botón Generar/Descargar
        try:
            generar = await page.find("Generar", best_match=True, timeout=15)
            await generar.click()
            await asyncio.sleep(5)
            await _snap(page, "06_post_generar")
        except Exception as e:
            print(f"[DEBUG] No se encontró botón Generar: {e}")

        content = await page.get_content()
        with open(destino, "wb") as f:
            f.write(content.encode() if isinstance(content, str) else content)

    finally:
        await browser.stop()

    return destino
