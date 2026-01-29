import requests
import pandas as pd
from bs4 import BeautifulSoup
from time import sleep

BASE_URL = "https://judiciales.elespectador.com/index.php"
DETALLE_URL = "https://judiciales.elespectador.com/detalle.php"

HEADERS = {
    "User-Agent": "EdictosBot/1.0 (automatizacion responsable)"
}

def buscar_edictos(session, palabras, fecha_ini, fecha_fin, page=1):
    data = {
        "palabras": palabras,
        "categoria": "",
        "validez_init": fecha_ini,
        "validez_fin": fecha_fin
    }

    if page == 1:
        r = session.post(BASE_URL, data=data, headers=HEADERS, timeout=20)
    else:
        r = session.get(f"{BASE_URL}?page={page}", headers=HEADERS, timeout=20)

    r.raise_for_status()
    return r.text


def obtener_detalle(session, idenv):
    params = {"idenv": idenv}
    r = session.get(DETALLE_URL, params=params, headers=HEADERS, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")

    detalle = soup.get_text(separator=" ", strip=True)
    return detalle


def parsear_pagina(html, session, pagina):
    soup = BeautifulSoup(html, "lxml")
    resultados = []

    bloques = soup.find_all("div", id="detalle_resultado")

    for bloque in bloques:
        resumen = bloque.get_text(strip=True)

        boton = bloque.find_next("button")
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
            texto = ubicacion.get_text(" ", strip=True)
            if "FECHA:" in texto:
                fecha = texto.split("FECHA:")[1].split("CATEGORÍA:")[0].strip()
            if "CATEGORÍA:" in texto:
                categoria = texto.split("CATEGORÍA:")[1].strip()

        print(f"  ↳ Detalle {idenv}")
        detalle = obtener_detalle(session, idenv)
        sleep(1)  

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

    PALABRA_CLAVE = "MORALES"
    FECHA_INI = "2026-01-01"
    FECHA_FIN = "2026-01-31"
    PAGINAS = 5  
    todos = []

    for page in range(1, PAGINAS + 1):
        print(f"Procesando página {page}")
        html = buscar_edictos(
            session,
            PALABRA_CLAVE,
            FECHA_INI,
            FECHA_FIN,
            page
        )

        resultados = parsear_pagina(html, session, page)
        todos.extend(resultados)
        sleep(2)

    df = pd.DataFrame(todos)
    df.to_excel("edictos_elespectador.xlsx", index=False)

    print("Excel generado: edictos_elespectador.xlsx")


if __name__ == "__main__":
    main()
