import os
from datetime import datetime
from playwright.async_api import async_playwright
from .auth import login_efirma
from config import DOCUMENTS_PATH

URL = "https://www.sat.gob.mx/consultas/59274/consulta-tu-opinion-de-cumplimiento-de-obligaciones-fiscales"


async def descargar_opinion() -> str:
    """Descarga la Opinión de Cumplimiento y retorna la ruta del PDF."""
    os.makedirs(DOCUMENTS_PATH, exist_ok=True)
    fecha = datetime.now().strftime("%Y-%m")
    destino = os.path.abspath(f"{DOCUMENTS_PATH}/opinion_cumplimiento_{fecha}.pdf")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        await page.goto(URL, wait_until="networkidle", timeout=60_000)
        await login_efirma(page)

        # Esperar que cargue la opinión
        await page.wait_for_selector(
            "button:has-text('Imprimir'), button:has-text('Descargar'), a:has-text('Opinión')",
            timeout=30_000,
        )

        # Intentar descarga directa; si no, imprimir a PDF
        dl_btn = page.locator("button:has-text('Descargar'), a[href*='.pdf']").first
        if await dl_btn.count() > 0:
            async with page.expect_download() as dl_info:
                await dl_btn.click()
            download = await dl_info.value
            await download.save_as(destino)
        else:
            # SAT muestra la opinión en pantalla → guardar como PDF
            await page.pdf(path=destino, format="Letter")

        await browser.close()

    return destino
