import os
import asyncio
from datetime import datetime
import nodriver as uc
from config import DOCUMENTS_PATH, SAT_EFIRMA_CER_PATH, SAT_EFIRMA_KEY_PATH, SAT_EFIRMA_PASSWORD, SAT_RFC

LOGIN_URL = "https://wwwmat.sat.gob.mx/personas/iniciar-sesion"
CONSTANCIA_URL = "https://wwwmat.sat.gob.mx/aplicacion/operacion/66862/constancia-de-situacion-fiscal"


async def descargar_constancia() -> str:
    os.makedirs(DOCUMENTS_PATH, exist_ok=True)
    fecha = datetime.now().strftime("%Y-%m")
    destino = os.path.abspath(f"{DOCUMENTS_PATH}/constancia_{fecha}.pdf")

    browser = await uc.start(headless=False, lang="es-MX")
    try:
        page = await browser.get(LOGIN_URL)
        await asyncio.sleep(3)
        print(f"[DEBUG] Login page: {page.url}")

        # Clic en botón "e.firma" para cambiar al formulario de e.firma
        efirma_btn = await page.find("e.firma", best_match=True, timeout=15)
        await efirma_btn.click()
        await asyncio.sleep(2)
        print("[DEBUG] Clic en e.firma — esperando formulario")
        await page.save_screenshot(f"{DOCUMENTS_PATH}/debug_01_efirma_form.png")

        # Subir .cer — puede ser file input o text input con el path
        file_inputs = await page.select_all("input[type='file']")
        print(f"[DEBUG] file inputs: {len(file_inputs)}")

        if len(file_inputs) >= 2:
            await file_inputs[0].send_file(SAT_EFIRMA_CER_PATH)
            await asyncio.sleep(1)
            await file_inputs[1].send_file(SAT_EFIRMA_KEY_PATH)
            print("[DEBUG] Archivos subidos via file input")
        else:
            # El portal MAT puede usar text inputs con la ruta del archivo
            cer_input = await page.select("input[placeholder*='certificado'], input[placeholder*='cer']", timeout=10)
            await cer_input.send_keys(SAT_EFIRMA_CER_PATH)
            key_input = await page.select("input[placeholder*='llave'], input[placeholder*='key']", timeout=10)
            await key_input.send_keys(SAT_EFIRMA_KEY_PATH)
            print("[DEBUG] Rutas escritas en text inputs")

        # Contraseña de clave privada
        pwd = await page.select("input[placeholder*='Contraseña'], input[type='password']", timeout=10)
        await pwd.send_keys(SAT_EFIRMA_PASSWORD)

        # RFC
        try:
            rfc_input = await page.select("input[placeholder='RFC']", timeout=5)
            await rfc_input.send_keys(SAT_RFC)
        except Exception:
            pass

        await page.save_screenshot(f"{DOCUMENTS_PATH}/debug_02_filled.png")

        # Enviar
        enviar = await page.find("Enviar", best_match=True, timeout=10)
        await enviar.click()
        await asyncio.sleep(6)
        print(f"[DEBUG] Post-login URL: {page.url}")
        await page.save_screenshot(f"{DOCUMENTS_PATH}/debug_03_post_login.png")

        # Navegar a constancia
        page = await browser.get(CONSTANCIA_URL)
        await asyncio.sleep(5)
        print(f"[DEBUG] Constancia URL: {page.url}")
        await page.save_screenshot(f"{DOCUMENTS_PATH}/debug_04_constancia.png")

        # Descargar PDF
        try:
            generar = await page.find("Generar", best_match=True, timeout=15)
            await generar.click()
            await asyncio.sleep(5)
        except Exception:
            pass

        content = await page.get_content()
        with open(destino, "wb") as f:
            f.write(content.encode() if isinstance(content, str) else content)

    finally:
        await browser.stop()

    return destino
