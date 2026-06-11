import os
import asyncio
from datetime import datetime
import nodriver as uc
from config import DOCUMENTS_PATH, SAT_EFIRMA_CER_PATH, SAT_EFIRMA_KEY_PATH, SAT_EFIRMA_PASSWORD

URL = "https://www.sat.gob.mx/aplicacion/operacion/66862/constancia-de-situacion-fiscal"


async def descargar_constancia() -> str:
    os.makedirs(DOCUMENTS_PATH, exist_ok=True)
    fecha = datetime.now().strftime("%Y-%m")
    destino = os.path.abspath(f"{DOCUMENTS_PATH}/constancia_{fecha}.pdf")

    browser = await uc.start(headless=False, lang="es-MX")
    try:
        page = await browser.get(URL)
        await asyncio.sleep(3)

        print(f"[DEBUG] URL={page.url}")

        # Esperar a que aparezca el formulario de autenticación
        # El SAT puede mostrar opciones de login - buscar e.firma
        await asyncio.sleep(2)

        # Intentar hacer clic en e.firma si aparece la selección
        try:
            efirma_btn = await page.find("e.firma", best_match=True, timeout=10)
            await efirma_btn.click()
            await asyncio.sleep(2)
            print("[DEBUG] Clic en e.firma")
        except Exception:
            print("[DEBUG] No se encontró botón e.firma, continuando...")

        # Subir archivos de e.firma
        try:
            cer_input = await page.select("input[type='file']", timeout=15)
            await cer_input.send_file(SAT_EFIRMA_CER_PATH)
            print("[DEBUG] .cer subido")
        except Exception as e:
            print(f"[DEBUG] Error subiendo .cer: {e}")

        try:
            file_inputs = await page.select_all("input[type='file']")
            if len(file_inputs) >= 2:
                await file_inputs[1].send_file(SAT_EFIRMA_KEY_PATH)
                print("[DEBUG] .key subido")
        except Exception as e:
            print(f"[DEBUG] Error subiendo .key: {e}")

        # Contraseña
        try:
            pwd = await page.select("input[type='password']", timeout=10)
            await pwd.send_keys(SAT_EFIRMA_PASSWORD)
            print("[DEBUG] Contraseña ingresada")
        except Exception as e:
            print(f"[DEBUG] Error en contraseña: {e}")

        # Submit
        try:
            submit = await page.find("Enviar", best_match=True, timeout=10)
            await submit.click()
        except Exception:
            try:
                submit = await page.select("button[type='submit'], input[type='submit']", timeout=10)
                await submit.click()
            except Exception as e:
                print(f"[DEBUG] Error en submit: {e}")

        await asyncio.sleep(5)
        print(f"[DEBUG] Post-login URL: {page.url}")

        # Descargar PDF vía print
        await page.save_screenshot(f"{DOCUMENTS_PATH}/debug_post_login.png")
        await page.get_content()

        # Guardar como PDF
        await page.set_download_path(os.path.abspath(DOCUMENTS_PATH))
        pdf = await page.get_content()
        with open(destino, "wb") as f:
            f.write(pdf.encode() if isinstance(pdf, str) else pdf)

    finally:
        await browser.stop()

    return destino
