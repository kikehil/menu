import os
import asyncio
from playwright.async_api import Page
from config import SAT_EFIRMA_CER_PATH, SAT_EFIRMA_KEY_PATH, SAT_EFIRMA_PASSWORD, DOCUMENTS_PATH

LOGIN_URL = "https://wwwmat.sat.gob.mx/personas/iniciar-sesion"


async def login_efirma(page: Page):
    """Inicia sesión en el portal MAT del SAT usando e.firma."""
    await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60_000)
    # Give JS frameworks time to render tabs
    await asyncio.sleep(3)
    await _snap(page, "01_login")

    # Dump ALL text nodes to find exact button label
    all_texts = await page.evaluate("""
        () => {
            const results = [];
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_ELEMENT,
                null, false
            );
            let node;
            while ((node = walker.nextNode())) {
                const txt = (node.innerText || node.textContent || '').trim();
                if (txt && txt.length > 0 && txt.length < 80 && node.children.length === 0) {
                    results.push({
                        tag: node.tagName,
                        text: txt,
                        id: node.id,
                        cls: node.className
                    });
                }
            }
            return results;
        }
    """)
    print(f"[DEBUG] Nodos de texto en página: {all_texts}")

    # Also dump clickable elements specifically
    clickable = await page.evaluate("""
        () => Array.from(document.querySelectorAll(
            'button, a, [role="tab"], [role="button"], input[type=button], input[type=submit], li[onclick], li[class*=tab], li[class*=nav]'
        )).map(e => ({
            tag: e.tagName,
            text: (e.innerText || e.textContent || e.value || '').trim(),
            href: e.href || '',
            id: e.id,
            cls: e.className
        })).filter(e => e.text)
    """)
    print(f"[DEBUG] Elementos clicables: {clickable}")

    # Try Playwright's own text locators first (most reliable)
    clicked = False
    for locator_str in [
        "text=e.firma",
        "text=efirma",
        "text=eFirma",
        "text=Efirma",
        "[href*='efirma']",
        "[href*='e-firma']",
        "[href*='firma']",
        "a:has-text('firma')",
        "li:has-text('firma')",
        "[role='tab']:has-text('firma')",
        "button:has-text('firma')",
    ]:
        try:
            loc = page.locator(locator_str).first
            if await loc.count() > 0 and await loc.is_visible():
                await loc.click()
                print(f"[DEBUG] Clicked via Playwright locator: {locator_str}")
                clicked = True
                break
        except Exception as e:
            print(f"[DEBUG] Locator {locator_str!r} falló: {e}")

    if not clicked:
        # Fallback: JS – search ALL elements (not just interactive ones) by text
        result = await page.evaluate("""
            () => {
                const candidates = Array.from(document.querySelectorAll('*'));
                for (const el of candidates) {
                    const own = (el.childNodes.length === 1 && el.childNodes[0].nodeType === 3)
                        ? el.childNodes[0].textContent.trim()
                        : (el.innerText || el.textContent || '').trim();
                    if (own.toLowerCase().includes('firma') && own.length < 40) {
                        el.click();
                        return 'clicked: ' + el.tagName + ' | ' + own;
                    }
                }
                return 'not found';
            }
        """)
        print(f"[DEBUG] JS fallback resultado: {result}")

    await asyncio.sleep(2)
    await _snap(page, "02_after_efirma_click")

    # Wait for file inputs (e.firma form)
    try:
        await page.wait_for_selector("input[type='file']", timeout=20_000)
        print("[DEBUG] Formulario e.firma visible (file inputs encontrados)")
    except Exception as e:
        # Take snap to see what's on screen
        await _snap(page, "02_ERROR_no_file_input")
        # Print current page text to understand what's shown
        body_text = await page.evaluate("() => document.body.innerText")
        print(f"[DEBUG] Texto de la página en error: {body_text[:2000]}")
        raise RuntimeError(f"No apareció el formulario de e.firma: {e}")

    # Upload .cer
    cer_input = page.locator("input[type='file']").nth(0)
    await cer_input.set_input_files(SAT_EFIRMA_CER_PATH)
    print("[DEBUG] .cer cargado")
    await asyncio.sleep(1)

    # Upload .key
    key_input = page.locator("input[type='file']").nth(1)
    await key_input.set_input_files(SAT_EFIRMA_KEY_PATH)
    print("[DEBUG] .key cargado")
    await asyncio.sleep(1)

    # Password
    pwd_input = page.locator("input[type='password']").first
    await pwd_input.fill(SAT_EFIRMA_PASSWORD)
    print("[DEBUG] Contraseña ingresada")
    await _snap(page, "03_filled")

    # Submit
    for submit_sel in [
        "button:has-text('Enviar')",
        "input[value='Enviar']",
        "button[type='submit']",
        "input[type='submit']",
    ]:
        try:
            btn = page.locator(submit_sel).first
            if await btn.count() > 0 and await btn.is_visible():
                await btn.click()
                print(f"[DEBUG] Submit via: {submit_sel}")
                break
        except Exception:
            pass

    await page.wait_for_load_state("networkidle", timeout=60_000)
    print(f"[DEBUG] Post-login URL: {page.url}")
    await _snap(page, "04_post_login")


async def _snap(page: Page, name: str):
    os.makedirs(DOCUMENTS_PATH, exist_ok=True)
    path = os.path.abspath(f"{DOCUMENTS_PATH}/debug_{name}.png")
    await page.screenshot(path=path, full_page=True)
    print(f"[DEBUG] snap → {path}")
