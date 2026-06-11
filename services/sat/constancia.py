import os
import asyncio
from datetime import datetime
import nodriver as uc
from config import DOCUMENTS_PATH, SAT_EFIRMA_CER_PATH, SAT_EFIRMA_KEY_PATH, SAT_EFIRMA_PASSWORD

SAT_HOME = "https://www.sat.gob.mx/inicio"
URL_CONSTANCIA = "https://www.sat.gob.mx/aplicacion/operacion/66862/constancia-de-situacion-fiscal"


async def descargar_constancia() -> str:
    os.makedirs(DOCUMENTS_PATH, exist_ok=True)
    fecha = datetime.now().strftime("%Y-%m")
    destino = os.path.abspath(f"{DOCUMENTS_PATH}/constancia_{fecha}.pdf")

    browser = await uc.start(headless=False, lang="es-MX")
    try:
        # 1. Ir al inicio del SAT para establecer sesión/cookies
        page = await browser.get(SAT_HOME)
        await asyncio.sleep(4)
        print(f"[DEBUG] Inicio SAT URL={page.url} title={await page.title()}")
        await page.save_screenshot(f"{DOCUMENTS_PATH}/debug_01_inicio.png")

        # 2. Buscar y clic en botón de inicio de sesión
        try:
            login_btn = await page.find("Iniciar sesión", best_match=True, timeout=10)
            await login_btn.click()
            await asyncio.sleep(3)
            print("[DEBUG] Clic en Iniciar sesión")
        except Exception:
            try:
                login_btn = await page.find("Entrar", best_match=True, timeout=5)
                await login_btn.click()
                await asyncio.sleep(3)
                print("[DEBUG] Clic en Entrar")
            except Exception as e:
                print(f"[DEBUG] No encontré botón login: {e}")

        await page.save_screenshot(f"{DOCUMENTS_PATH}/debug_02_post_login_click.png")
        print(f"[DEBUG] URL post-click: {page.url}")

        # 3. Seleccionar e.firma si aparece la selección
        await asyncio.sleep(2)
        try:
            efirma = await page.find("e.firma", best_match=True, timeout=10)
            await efirma.click()
            await asyncio.sleep(3)
            print("[DEBUG] Clic en e.firma")
        except Exception as e:
            print(f"[DEBUG] No se encontró e.firma: {e}")

        await page.save_screenshot(f"{DOCUMENTS_PATH}/debug_03_efirma.png")

        # 4. Subir archivos de e.firma
        await asyncio.sleep(2)
        try:
            file_inputs = await page.select_all("input[type='file']")
            print(f"[DEBUG] {len(file_inputs)} inputs file encontrados")
            if len(file_inputs) >= 1:
                await file_inputs[0].send_file(SAT_EFIRMA_CER_PATH)
                print("[DEBUG] .cer subido")
            if len(file_inputs) >= 2:
                await file_inputs[1].send_file(SAT_EFIRMA_KEY_PATH)
                print("[DEBUG] .key subido")
        except Exception as e:
            print(f"[DEBUG] Error subiendo archivos: {e}")

        # 5. Contraseña y submit
        try:
            pwd = await page.select("input[type='password']", timeout=10)
            await pwd.send_keys(SAT_EFIRMA_PASSWORD)
            await asyncio.sleep(1)
            submit = await page.select("button[type='submit'], input[type='submit']", timeout=10)
            await submit.click()
            await asyncio.sleep(5)
            print(f"[DEBUG] Post-auth URL: {page.url}")
        except Exception as e:
            print(f"[DEBUG] Error en autenticación: {e}")

        await page.save_screenshot(f"{DOCUMENTS_PATH}/debug_04_post_auth.png")

        # 6. Navegar a constancia
        page = await browser.get(URL_CONSTANCIA)
        await asyncio.sleep(4)
        print(f"[DEBUG] Constancia URL: {page.url}")
        await page.save_screenshot(f"{DOCUMENTS_PATH}/debug_05_constancia.png")

        # 7. Descargar PDF
        pdf_bytes = await page.get_content()
        with open(destino, "wb") as f:
            f.write(pdf_bytes.encode() if isinstance(pdf_bytes, str) else pdf_bytes)

    finally:
        await browser.stop()

    return destino
