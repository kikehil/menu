import os
from datetime import datetime
from playwright.async_api import async_playwright
from .auth import login_efirma, _snap
from config import DOCUMENTS_PATH

OPINION_URL = "https://wwwmat.sat.gob.mx/aplicacion/operacion/22413/consulta-tu-opinion-de-cumplimiento-de-obligaciones-fiscales"


async def descargar_opinion() -> str:
    """Inicia sesión con e.firma y descarga la Opinión de Cumplimiento."""
    os.makedirs(DOCUMENTS_PATH, exist_ok=True)
    fecha = datetime.now().strftime("%Y-%m")
    destino = os.path.abspath(f"{DOCUMENTS_PATH}/opinion_cumplimiento_{fecha}.pdf")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        await login_efirma(page)

        await page.goto(OPINION_URL, wait_until="networkidle", timeout=60_000)
        await _snap(page, "05_opinion")
        print(f"[DEBUG] Opinión URL: {page.url}")

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
