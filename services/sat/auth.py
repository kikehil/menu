import os
from playwright.async_api import Page
from config import SAT_EFIRMA_CER_PATH, SAT_EFIRMA_KEY_PATH, SAT_EFIRMA_PASSWORD, DOCUMENTS_PATH

# URL directa al formulario de e.firma (sin pasar por la selección de tarjetas)
EFIRMA_LOGIN_URL = "https://cfdiau.sat.gob.mx/nidp/app/login?id=SATUPCFDiCFDi&sid=0&option=credential&sid=0"


async def login_efirma(page: Page):
    # Ir directamente al formulario de e.firma
    await page.goto(EFIRMA_LOGIN_URL, wait_until="domcontentloaded", timeout=60_000)

    # Esperar a que aparezca algún input de archivo
    await page.wait_for_selector("input[type='file']", timeout=30_000)

    # Captura para debug
    screenshot = os.path.abspath(f"{DOCUMENTS_PATH}/debug_login.png")
    await page.screenshot(path=screenshot)
    print(f"[DEBUG] Login URL: {page.url}")
    print(f"[DEBUG] Login screenshot: {screenshot}")

    # Subir .cer
    inputs = await page.query_selector_all("input[type='file']")
    print(f"[DEBUG] inputs type=file encontrados: {len(inputs)}")
    for i, inp in enumerate(inputs):
        accept = await inp.get_attribute("accept") or ""
        name = await inp.get_attribute("name") or ""
        id_ = await inp.get_attribute("id") or ""
        print(f"[DEBUG] input[{i}] accept={accept!r} name={name!r} id={id_!r}")

    # Subir .cer (primer input de archivo)
    await page.set_input_files("input[type='file']:nth-of-type(1)", SAT_EFIRMA_CER_PATH)

    # Subir .key (segundo input de archivo)
    await page.set_input_files("input[type='file']:nth-of-type(2)", SAT_EFIRMA_KEY_PATH)

    # Contraseña
    password_input = page.locator("input[type='password']").first
    await password_input.fill(SAT_EFIRMA_PASSWORD)

    # Submit
    await page.click("button[type='submit'], input[type='submit']")
    await page.wait_for_load_state("networkidle", timeout=60_000)
    print(f"[DEBUG] Post-login URL: {page.url}")
