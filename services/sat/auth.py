import os
from playwright.async_api import Page, BrowserContext
from config import SAT_EFIRMA_CER_PATH, SAT_EFIRMA_KEY_PATH, SAT_EFIRMA_PASSWORD, DOCUMENTS_PATH

LOGIN_URL = "https://wwwmat.sat.gob.mx/personas/iniciar-sesion"


async def login_efirma(page: Page):
    """
    Inicia sesión en el portal MAT del SAT usando e.firma.
    Deja la sesión activa en el contexto del navegador.
    """
    await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60_000)

    # Esperar a que cargue el formulario de acceso por contraseña
    await page.wait_for_selector("text=Acceso por contraseña", timeout=30_000)
    await _snap(page, "01_login")

    # Debug: imprimir todos los botones visibles
    btns_text = await page.evaluate("""
        () => Array.from(document.querySelectorAll('button, input[type=button], input[type=submit], a'))
             .map(e => e.tagName + ':' + (e.innerText || e.value || e.textContent || '').trim())
             .filter(t => t.split(':')[1])
    """)
    print(f"[DEBUG] Elementos clicables: {btns_text}")

    # Clic en el botón "e.firma" para cambiar al formulario de e.firma
    clicked = await page.evaluate("""
        () => {
            const els = Array.from(document.querySelectorAll('button, input[type=button], input[type=submit], a'));
            for (const el of els) {
                const txt = (el.innerText || el.value || el.textContent || '').trim();
                if (txt.toLowerCase().includes('e.firma') || txt.toLowerCase().includes('efirma')) {
                    el.click();
                    return 'clicked: ' + txt;
                }
            }
            return 'not found';
        }
    """)
    print(f"[DEBUG] Click resultado: {clicked}")

    # Esperar el formulario de e.firma (campo Certificado)
    await page.wait_for_selector("text=Certificado", timeout=30_000)
    await _snap(page, "02_efirma_form")

    # Subir certificado (.cer) — el botón "Buscar" abre un file input
    cer_input = page.locator("input[type='file']").nth(0)
    await cer_input.set_input_files(SAT_EFIRMA_CER_PATH)
    print("[DEBUG] .cer cargado")

    # Subir llave privada (.key)
    key_input = page.locator("input[type='file']").nth(1)
    await key_input.set_input_files(SAT_EFIRMA_KEY_PATH)
    print("[DEBUG] .key cargado")

    # Contraseña de la clave privada
    await page.fill("input[type='password']", SAT_EFIRMA_PASSWORD)
    print("[DEBUG] Contraseña ingresada")

    await _snap(page, "03_filled")

    # Clic en Enviar
    await page.click("button:has-text('Enviar'), input[value='Enviar']")
    print("[DEBUG] Formulario enviado, esperando autenticación...")

    # Esperar la redirección post-login
    await page.wait_for_load_state("networkidle", timeout=60_000)
    print(f"[DEBUG] Post-login URL: {page.url}")
    await _snap(page, "04_post_login")


async def _snap(page: Page, name: str):
    os.makedirs(DOCUMENTS_PATH, exist_ok=True)
    path = os.path.abspath(f"{DOCUMENTS_PATH}/debug_{name}.png")
    await page.screenshot(path=path, full_page=True)
    print(f"[DEBUG] snap → {path}")
