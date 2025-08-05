from playwright.sync_api import sync_playwright
from geopy.geocoders import GoogleV3
import time
import json
import os
import re
import sqlite3

# --- Rutas y DB ---
DB_PATH = os.path.join(os.path.dirname(__file__), 'multas.db')
CARPETA_FOTOS = "evidencias"

# --- Función de limpieza para obtener solo el ID del acta ---
def limpiar_id_acta(texto_acta_completo):
    if not isinstance(texto_acta_completo, str): return ""
    match = re.search(r'([A-Z]\d+)', texto_acta_completo)
    return match.group(1) if match else texto_acta_completo.strip()

# --- Función para leer patentes desde la DB ---
def obtener_patentes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT patente FROM patentes")
    filas = cursor.fetchall()
    conn.close()
    return [fila[0] for fila in filas]

# --- Funciones para consultar si multa existe e insertar multa ---
def multa_existe(id_acta):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM multas WHERE id_multa = ?", (id_acta,))
    existe = cursor.fetchone() is not None
    conn.close()
    return existe

def insertar_multa(multa):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()  # Asegurarse de definir cursor antes de cualquier uso

        # Verificar si ya existe la multa
        cursor.execute("SELECT COUNT(*) FROM multas WHERE id_multa = ?", (multa["Acta"],))
        existe = cursor.fetchone()[0]

        if existe == 0:
            cursor.execute("""
                INSERT INTO multas (id_multa, acta, fecha, motivo, lugar, latitud, longitud, codigos)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                multa["Acta"],
                multa["Acta"],
                multa["Fecha"],
                multa["Motivo"],
                multa["Lugar"],
                multa["Latitud"],
                multa["Longitud"],
                json.dumps(multa["Codigos"], ensure_ascii=False)
            ))
            print(f"  - Multa insertada: {multa['Acta']}")
        else:
            print(f"  - Multa ya existente en base: {multa['Acta']} (omitida)")

        conn.commit()
    except Exception as e:
        print(f"Ocurrió un error general en insertar_multa: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

# --- Función principal de scraping (modificada para iterar todas las patentes) ---
def correr_script_json(playwright):
    geolocator = GoogleV3(api_key="AIzaSyAFUPi6JZI0R4hKqFR-7isnjwsK0IZZ93Q")

    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    
    print("\n--- INICIANDO SCRIPT (DB + Geocoding) ---")

    patentes = obtener_patentes()
    if not patentes:
        print("No se encontraron patentes en la base de datos.")
        browser.close()
        return

    try:
        url_caba = "https://buenosaires.gob.ar/licenciasdeconducir/consulta-de-infracciones/?actas=transito"
        for patente in patentes:
            print(f"Consultando patente: {patente}")
            page.goto(url_caba, timeout=60000)
            page.locator("text='Una patente'").click()
            page.locator("#edit-dominio").fill(patente)
            frame_locator = page.frame_locator('[title="reCAPTCHA"]')
            frame_locator.locator("div.recaptcha-checkbox-border").click()
            time.sleep(2)
            page.locator("button:has-text('Consultar')").click()
            print("Login exitoso.")
            page.wait_for_selector("button.card-header:has(.collapse-label)", timeout=60000)

            multas = page.locator("button.card-header:has(.collapse-label)").all()
            nuevas_multas = 0
            for multa_element in multas:
                acta_completa = multa_element.locator(".collapse-label").inner_text()
                id_acta = limpiar_id_acta(acta_completa)









                if not multa_existe(id_acta):
                    nuevas_multas += 1
                    print(f"  - Nueva infracción encontrada: {id_acta}")
                    partes = acta_completa.split(' - ')
                    fecha = partes[1].strip() if len(partes) > 1 else "No encontrada"
                    motivo = multa_element.locator(".collapse-title").inner_text()

                    if multa_element.get_attribute("aria-expanded") == "false":
                        multa_element.click(force=True)
                        time.sleep(0.5)

                    contenedor_multa = multa_element.locator("xpath=..")
                    lugar_locator = contenedor_multa.locator("xpath=.//h5[normalize-space()='Lugar:']/following-sibling::span")
                    lugar = lugar_locator.inner_text() if lugar_locator.count() > 0 else "No encontrada"

                    latitud, longitud = "No encontrada", "No encontrada"
                    lugar_completo = "No encontrado"
                    if "No encontrado" not in lugar:
                        lugar_completo = f"{lugar.strip()}, Ciudad Autónoma de Buenos Aires, Argentina"
                        print(f"    - Geolocalizando con Google: '{lugar_completo}'...")
                        try:
                            location = geolocator.geocode(lugar_completo, timeout=10)
                            if location:
                                latitud, longitud = location.latitude, location.longitude
                        except Exception as geoloc_error:
                            print(f"    - Error de geolocalización: {geoloc_error}")

                    input_checkbox = multa_element.locator("input.rowcheckbox")
                    codigos = []
                    if input_checkbox.count() > 0:
                        try:
                            data_json_str = input_checkbox.get_attribute('data-json')
                            data_json = json.loads(data_json_str)
                            codigos = [infraccion['infraccion'] for infraccion in data_json.get('infracciones', [])]
                        except Exception as e:
                            print(f"  - No se pudieron extraer los códigos de infracción: {e}")

                    multa = {
                        "Acta": acta_completa.strip(),
                        "Patente": patente,
                        "Fecha": fecha,
                        "Motivo": motivo.strip(),
                        "Lugar": lugar_completo,
                        "Latitud": latitud,
                        "Longitud": longitud,
                        "Codigos": codigos
                    }

                    try:
                        insertar_multa(multa)
                    except Exception as e:
                        print(f"  - Error al insertar multa {id_acta}: {e}")
                else:
                    print(f"  - Multa ya existente: {id_acta} (omitida)")
 
                    insertar_multa(multa)

            if nuevas_multas == 0:
                print("  No hay multas nuevas para guardar.")
            else:
                print(f"  Se agregaron {nuevas_multas} multas nuevas para patente {patente}.")

    except Exception as e:
        print(f"\nOcurrió un error general: {e}")
    finally:
        browser.close()
        print("--- SCRIPT (DB) FINALIZADO ---")

# --- SCRIPT 2: TAREA DE FOTOS (SIN CAMBIOS) ---
def correr_script_fotos(playwright):
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    print("\n--- INICIANDO SCRIPT 2 (FOTOS) ---")
    try:
        url_caba = "https://buenosaires.gob.ar/licenciasdeconducir/consulta-de-infracciones/?actas=transito"
        page.goto(url_caba, timeout=60000)

        print("Iniciando sesión (para fotos)...")
        # Aquí habría que iterar también las patentes, pero si querés mantengo hardcode o hacemos bucle
        # Por simplicidad, lo dejamos hardcode para que uses la última patente de la lista
        patentes = obtener_patentes()
        if not patentes:
            print("No hay patentes para procesar fotos.")
            return
        ultima_patente = patentes[-1]

        page.locator("text='Una patente'").click()
        page.locator("#edit-dominio").fill(ultima_patente)
        frame_locator = page.frame_locator('[title="reCAPTCHA"]')
        frame_locator.locator("div.recaptcha-checkbox-border").click()
        time.sleep(2)
        page.locator("button:has-text('Consultar')").click()
        print("Login exitoso.")

        total_multas = 0
        try:
            contador_element = page.locator("h6:has-text('Infracciones totales')")
            contador_element.wait_for(state="visible", timeout=10000)
            texto_contador = contador_element.inner_text()
            numeros_encontrados = re.findall(r'\d+', texto_contador)
            total_multas = int(numeros_encontrados[0]) if numeros_encontrados else 0
        except:
            pass

        if total_multas == 0:
            print("No se encontraron infracciones pendientes.")
            return

        print(f"La página indica un total de {total_multas} infracciones.")
        expression = f"() => document.querySelectorAll('button.card-header').length >= {total_multas}"
        page.wait_for_function(expression, timeout=30000)
        print("¡Todas las multas están cargadas!")

        print("\n--- PROCESANDO INFRACCIONES (SOLO FOTOS) ---\n")
        multas = page.locator("button.card-header").all()

        for i in range(total_multas):
            multa_element = multas[i]
            acta_completa = multa_element.locator(".collapse-label").inner_text() if multa_element.locator(".collapse-label").count() > 0 else f"Acta_desconocida_{i+1}"
            id_acta = limpiar_id_acta(acta_completa)

            print(f"Procesando infracción #{i+1} para foto: {id_acta}")
            try:
                print("  Expandiendo multa con clic forzado...")
                multa_element.click(force=True)
                time.sleep(1)

                contenedor_multa = multa_element.locator("xpath=..")
                boton_descarga = contenedor_multa.locator(".descargar_imagen_pdf")
                if boton_descarga.count() > 0:
                    print("  Intentando descarga...")
                    with context.expect_page(timeout=10000) as new_page_info:
                        boton_descarga.click(force=True)
                    new_page = new_page_info.value
                    new_page.wait_for_load_state()
                    time.sleep(3)
                    nombre_archivo_png = f"{id_acta}.png"
                    ruta_guardado = os.path.join(CARPETA_FOTOS, nombre_archivo_png)
                    new_page.screenshot(path=ruta_guardado, full_page=True)
                    print(f"  Evidencia guardada en: {ruta_guardado}")
                    new_page.close()
                else:
                    print("  - No se encontró botón de descarga.")
            except Exception as e:
                print(f"  - Ocurrió un error en la expansión o descarga. Error: {e}")

            print("-" * 30)

    except Exception as e:
        print(f"\nOcurrió un error general: {e}")
    finally:
        print("\nScraper finalizado.")
        browser.close()
        print("--- SCRIPT 2 (FOTOS) FINALIZADO ---")

# --- Flujo Principal ---
if __name__ == "__main__":
    with sync_playwright() as playwright:
        correr_script_json(playwright)

        print("\n--- PAUSA DE 5 SEGUNDOS ANTES DE INICIAR SCRIPT DE FOTOS ---")
        time.sleep(5)

        correr_script_fotos(playwright)
