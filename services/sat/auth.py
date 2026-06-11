import os
from playwright.async_api import Page
from config import SAT_EFIRMA_CER_PATH, SAT_EFIRMA_KEY_PATH, SAT_EFIRMA_PASSWORD, DOCUMENTS_PATH


async def login_efirma(page: Page):
    """
    Asume que la página ya fue redirigida al login del SAT (NIDP).
    Espera las tarjetas de autenticación, hace clic en e.firma y llena las credenciales.
    """
    # Esperar a que la página esté lista
    await page.wait_for_load_state("domcontentloaded", timeout=30_000)

    await _snap(page, "01_login_page")

    current_url = page.url
    print(f"[DEBUG] URL en login_efirma: {current_url}")

    # Si estamos en la página de selección de tarjetas, hacer clic en e.firma
    if "nidp" in current_url:
        # Esperar a que aparezca algún enlace/botón de autenticación
        await page.wait_for_function(
            "document.querySelectorAll('a, button, li').length > 5",
            timeout=20_000,
        )
        await _snap(page, "02_cards_loaded")

        # Buscar opción e.firma (varios posibles selectores)
        efirma = page.locator(
            "a[href*='Efirma'], a[href*='efirma'], a[href*='x509'], "
            "a:has-text('e.firma'), li:has-text('e.firma'), "
            "span:has-text('e.firma'), div:has-text('e.firma')"
        ).first

        if await efirma.count() > 0:
            print("[DEBUG] Clic en e.firma")
            await efirma.click()
            await page.wait_for_load_state("networkidle", timeout=30_000)
            await _snap(page, "03_after_efirma_click")
        else:
            # Imprimir todos los enlaces visibles para debug
            links = await page.eval_on_selector_all("a", "els => els.map(e => ({href: e.href, text: e.innerText.trim()}))")
            print(f"[DEBUG] enlaces en la página: {links[:20]}")

    # Esperar el formulario de e.firma
    await page.wait_for_selector("input[type='file']", timeout=30_000)
    await _snap(page, "04_efirma_form")

    inputs = await page.query_selector_all("input[type='file']")
    print(f"[DEBUG] {len(inputs)} input[type=file] encontrados")
    for i, inp in enumerate(inputs):
        print(f"[DEBUG]  [{i}] accept={await inp.get_attribute('accept')!r} name={await inp.get_attribute('name')!r}")

    if len(inputs) >= 2:
        await inputs[0].set_input_files(SAT_EFIRMA_CER_PATH)
        await inputs[1].set_input_files(SAT_EFIRMA_KEY_PATH)
    elif len(inputs) == 1:
        # Algunos portales usan un solo input
        await inputs[0].set_input_files(SAT_EFIRMA_CER_PATH)

    await page.fill("input[type='password']", SAT_EFIRMA_PASSWORD)
    await page.click("button[type='submit'], input[type='submit'], #btnEntrar")
    await page.wait_for_load_state("networkidle", timeout=60_000)
    print(f"[DEBUG] Post-login URL: {page.url}")
    await _snap(page, "05_post_login")


async def _snap(page: Page, name: str):
    path = os.path.abspath(f"{DOCUMENTS_PATH}/debug_{name}.png")
    await page.screenshot(path=path)
    print(f"[DEBUG] screenshot → {path}")
