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
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            accept_downloads=True,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()
        from playwright_stealth import stealth_async
        await stealth_async(page)

        await page.goto(URL, wait_until="networkidle", timeout=60_000)
        snap = os.path.abspath(f"{DOCUMENTS_PATH}/debug_01_constancia.png")
        await page.screenshot(path=snap, full_page=True)
        print(f"[DEBUG] URL={page.url}  title={await page.title()}")

        # Imprimir iframes encontrados
        frames = page.frames
        print(f"[DEBUG] frames en la página: {len(frames)}")
        for i, f in enumerate(frames):
            print(f"[DEBUG]  frame[{i}] url={f.url}")

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
