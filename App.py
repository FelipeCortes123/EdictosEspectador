import requests
import pandas as pd
from bs4 import BeautifulSoup
from time import sleep

# ================== CONFIGURACIÓN ==================

BASE_URL = "https://judiciales.elespectador.com/index.php"
DETALLE_URL = "https://judiciales.elespectador.com/detalle.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; EdictosBot/1.0; +automatizacion-responsable)"
}

PALABRA_CLAVE = "MORALES"
FECHA_INI = "2026-01-01"
FECHA_FIN = "2026-01-31"
MAX_PAGINAS = 5           # puedes subirlo luego
SLEEP_DETALLE = 1         # segundos entre edictos
SLEEP_PAGINA = 2          # segundos entre páginas

# ====================================================


def buscar_edictos(session, page=1):
    """
    Realiza la búsqueda inicial (POST) y luego la paginación (GET)
    """
    data = {
        "palabras": PALABRA_CLAVE,
        "categoria": "",
        "validez_init": FECHA_INI,
        "validez_fin": FECHA_FIN
    }

    if page == 1:
        r = session.post(BASE_URL, data=data, headers=HEADERS, timeout=20)
    else:
        r = session.get(f"{BASE_URL}?page={page}", headers=HEADERS, timeout=20)

    r.raise_for_status()
    return r.text


def obtener_detalle(session, idenv):
    """
    Entra al detalle.php y devuelve el texto completo del edicto
    """
    params = {"idenv": idenv}
    r = session.get(DETALLE_URL, params=params, headers=HEADERS, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")

    # Texto limpio del edicto (HTML suele venir muy plano)
    texto = soup.get_text(separator=" ", strip=True)

    return texto


def parsear_pagina(html, session, pagina):
    """
    Parsea una página de resultados y entra a cada detalle
    """
    soup = BeautifulSoup(html, "lxml")
    resultados = []

    bloques = soup.find_all("div", id="detalle_resultado")

    for bloque in bloques:
        resumen = bloque.get_text(" ", strip=True)

        # Algunos bloques vienen vacíos → se omiten
        if not resumen:
            continue

        boton = bloque.find_next("button", onclick=True)
        if not boton:
            continue

        onclick = boton.get("onclick", "")
        if "loaddtail" not in onclick:
            continue

        idenv = onclick.split("'")[1]

        ubicacion = boton.find_next("div", id="ubicacion")
        fecha = ""
        categoria = ""

        if ubicacion:
            texto_meta = ubicacion.get_text(" ", strip=True)
            if "FECHA:" in texto_meta:
                fecha = texto_meta.split("FECHA:")[1].split("CATEGORÍA:")[0].strip()
            if "CATEGORÍA:" in texto_meta:
                categoria = texto_meta.split("CATEGORÍA:")[1].strip()

        print(f"    ↳ Obteniendo detalle {idenv}")

        try:
            detalle = obtener_detalle(session, idenv)
        except Exception as e:
            print(f"      ⚠ Error en detalle {idenv}: {e}")
            detalle = ""

        sleep(SLEEP_DETALLE)

        resultados.append({
            "id_edicto": idenv,
            "fecha": fecha,
            "categoria": categoria,
            "resumen": resumen,
            "detalle_completo": detalle,
            "url_detalle": f"{DETALLE_URL}?idenv={idenv}",
            "pagina": pagina
        })

    return resultados


def main():
    session = requests.Session()
    todos_los_edictos = []

    for page in range(1, MAX_PAGINAS + 1):
        print(f"📄 Procesando página {page}")

        html = buscar_edictos(session, page)
        resultados = parsear_pagina(html, session, page)

        print(f"   ✔ {len(resultados)} edictos encontrados en página {page}")

        todos_los_edictos.extend(resultados)
        sleep(SLEEP_PAGINA)

    df = pd.DataFrame(todos_los_edictos)

    df.to_excel("edictos_elespectador.xlsx", index=False)
    print(f"\n✅ Excel generado correctamente con {len(df)} edictos")
    print("📁 Archivo: edictos_elespectador.xlsx")


if __name__ == "__main__":
    main()
