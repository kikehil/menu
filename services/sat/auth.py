from playwright.async_api import Page
from config import SAT_EFIRMA_CER_PATH, SAT_EFIRMA_KEY_PATH, SAT_EFIRMA_PASSWORD

SAT_LOGIN_URL = "https://cfdiau.sat.gob.mx/nidp/app/login?id=SATUPCFDiCFDi&sid=0&option=credential&sid=0"


async def login_efirma(page: Page):
    await page.goto(SAT_LOGIN_URL, wait_until="networkidle", timeout=60_000)

    # Seleccionar pestaña e.firma si existe
    efirma_tab = page.locator("a:has-text('e.firma'), #tab-fiel, [data-tab='fiel']").first
    if await efirma_tab.count() > 0:
        await efirma_tab.click()

    # Subir archivos de e.firma
    await page.set_input_files(
        "input[type='file'][accept*='.cer'], #certFile, input[name='certFile']",
        SAT_EFIRMA_CER_PATH,
    )
    await page.set_input_files(
        "input[type='file'][accept*='.key'], #keyFile, input[name='keyFile']",
        SAT_EFIRMA_KEY_PATH,
    )

    # Ingresar contraseña de e.firma
    await page.fill(
        "#fiel_password, input[name='fiel_password'], input[type='password']",
        SAT_EFIRMA_PASSWORD,
    )

    # Enviar formulario
    await page.click("button[type='submit'], input[type='submit'], #btnEntrar")
    await page.wait_for_load_state("networkidle", timeout=60_000)
