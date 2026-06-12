import os
from datetime import datetime
from playwright.async_api import async_playwright
from .auth import login_efirma, _snap
from config import DOCUMENTS_PATH

CONSTANCIA_URL = "https://wwwmat.sat.gob.mx/aplicacion/login/53027/genera-tu-constancia-de-situacion-fiscal"


async def descargar_constancia() -> str:
    """Inicia sesión con e.firma y descarga la Constancia de Situación Fiscal."""
    os.makedirs(DOCUMENTS_PATH, exist_ok=True)
    fecha = datetime.now().strftime("%Y-%m")
    destino = os.path.abspath(f"{DOCUMENTS_PATH}/constancia_{fecha}.pdf")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        # Autenticar con e.firma
        await login_efirma(page)

        # Navegar al generador de constancia
        await page.goto(CONSTANCIA_URL, wait_until="networkidle", timeout=60_000)
        await _snap(page, "05_constancia")
        print(f"[DEBUG] Constancia URL: {page.url}")

        # Buscar y hacer clic en el botón de generar/descargar PDF
        # El SAT genera el PDF y lo ofrece como descarga
        try:
            async with page.expect_download(timeout=30_000) as dl_info:
                await page.click(
                    "button:has-text('Generar'), a:has-text('Generar'), "
                    "button:has-text('Descargar'), a:has-text('Descargar'), "
                    "button:has-text('Imprimir'), a:has-text('Imprimir')"
                )
            download = await dl_info.value
            await download.save_as(destino)
            print(f"[DEBUG] PDF descargado: {destino}")
        except Exception as e:
            print(f"[DEBUG] No hubo descarga directa ({e}), generando PDF de la página")
            await page.pdf(path=destino, format="Letter")

        await browser.close()

    return destino
