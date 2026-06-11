import os
from datetime import datetime
from playwright.async_api import async_playwright
from .auth import login_efirma
from config import DOCUMENTS_PATH

URL = "https://www.sat.gob.mx/aplicacion/operacion/66862/constancia-de-situacion-fiscal"


async def descargar_constancia() -> str:
    os.makedirs(DOCUMENTS_PATH, exist_ok=True)
    fecha = datetime.now().strftime("%Y-%m")
    destino = os.path.abspath(f"{DOCUMENTS_PATH}/constancia_{fecha}.pdf")

    async with async_playwright() as p:
        # headless=False para ver qué pasa en el portal del SAT
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        await page.goto(URL, wait_until="networkidle", timeout=60_000)

        # Captura pantalla para debug
        screenshot = os.path.abspath(f"{DOCUMENTS_PATH}/debug_sat.png")
        await page.screenshot(path=screenshot)
        print(f"[DEBUG] Captura guardada en: {screenshot}")
        print(f"[DEBUG] URL actual: {page.url}")
        print(f"[DEBUG] Título: {await page.title()}")

        await login_efirma(page)

        await page.wait_for_selector(
            "button:has-text('Generar'), button:has-text('Descargar'), a:has-text('Constancia')",
            timeout=30_000,
        )

        async with page.expect_download() as dl_info:
            await page.click(
                "button:has-text('Generar'), button:has-text('Descargar'), a:has-text('Constancia')"
            )

        download = await dl_info.value
        await download.save_as(destino)
        await browser.close()

    return destino
