import os
import json
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin

CARPETA_DATA = "data"

CABECERAS = {
    "User-Agent": "Mozilla/5.0 RadikalSonoro/1.0"
}

FUENTES_RSS = [
    ("MariskalRock", "https://mariskalrock.com/feed/"),
    ("Metal Injection", "https://metalinjection.net/feed/"),
    ("Dying Scene", "https://dyingscene.com/feed/"),
    ("IDIOTEQ", "https://idioteq.com/feed/"),
]

PALABRAS_CLAVE = [
    "punk", "hardcore", "ska", "oi!", "oi ",
    "street punk", "crust", "d-beat", "anarcho",
    "post-punk", "punk rock", "metal", "heavy metal",
    "thrash", "death metal", "black metal",
    "grindcore", "metalcore", "powerviolence",
    "grunge", "underground", "independent",
    "independiente", "festival", "concierto",
    "gira", "banda", "bandas", "disco", "álbum",
    "album", "single", "ep ", "sello", "hardcore punk"
]


def fecha_actual():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def convertir_fecha(valor):
    if not valor:
        return fecha_actual()

    try:
        fecha = parsedate_to_datetime(valor)
        return fecha.strftime("%Y-%m-%d")
    except Exception:
        return fecha_actual()


def es_relevante(titulo, descripcion=""):
    texto = (titulo + " " + descripcion).lower()
    return any(palabra in texto for palabra in PALABRAS_CLAVE)


def leer_rss(nombre, url):
    noticias = []

    try:
        respuesta = requests.get(
            url,
            headers=CABECERAS,
            timeout=25
        )
        respuesta.raise_for_status()

        raiz = ET.fromstring(respuesta.content)

        elementos = raiz.findall(".//item")

        if not elementos:
            elementos = raiz.findall(
                ".//{http://www.w3.org/2005/Atom}entry"
            )

        for item in elementos:
            titulo = item.findtext("title")

            if titulo is None:
                titulo_elemento = item.find(
                    "{http://www.w3.org/2005/Atom}title"
                )
                titulo = titulo_elemento.text if titulo_elemento is not None else ""

            enlace = item.findtext("link")

            if not enlace:
                enlace_elemento = item.find(
                    "{http://www.w3.org/2005/Atom}link"
                )
                if enlace_elemento is not None:
                    enlace = enlace_elemento.attrib.get("href", "")

            descripcion = (
                item.findtext("description")
                or item.findtext(
                    "{http://www.w3.org/2005/Atom}summary"
                )
                or ""
            )

            fecha = (
                item.findtext("pubDate")
                or item.findtext(
                    "{http://www.w3.org/2005/Atom}published"
                )
                or item.findtext(
                    "{http://www.w3.org/2005/Atom}updated"
                )
            )

            if not titulo or not enlace:
                continue

            enlace = urljoin(url, enlace)

            if es_relevante(titulo, descripcion):
                noticias.append({
                    "titulo": titulo.strip(),
                    "url": enlace,
                    "fuente": nombre,
                    "fecha": convertir_fecha(fecha)
                })

        print(f"{nombre}: {len(noticias)} noticias")

    except Exception as error:
        print(f"No se pudo leer {nombre}: {error}")

    return noticias


def leer_insonoro():
    noticias = []
    url = "https://www.insonoro.com/"

    try:
        respuesta = requests.get(
            url,
            headers=CABECERAS,
            timeout=25
        )
        respuesta.raise_for_status()

        soup = BeautifulSoup(
            respuesta.text,
            "html.parser"
        )

        vistos = set()

        for enlace in soup.find_all("a", href=True):
            titulo = enlace.get_text(" ", strip=True)
            destino = urljoin(url, enlace["href"])

            if len(titulo) < 15:
                continue

            if destino in vistos:
                continue

            vistos.add(destino)

            if es_relevante(titulo):
                noticias.append({
                    "titulo": titulo,
                    "url": destino,
                    "fuente": "Insonoro",
                    "fecha": fecha_actual()
                })

            if len(noticias) >= 30:
                break

        print(f"Insonoro: {len(noticias)} noticias")

    except Exception as error:
        print(f"Error leyendo Insonoro: {error}")

    return noticias


def guardar_json(nombre, contenido):
    os.makedirs(CARPETA_DATA, exist_ok=True)

    ruta = os.path.join(CARPETA_DATA, nombre)

    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(
            contenido,
            archivo,
            ensure_ascii=False,
            indent=2
        )


def main():
    print("RADIKAL SONORO - ACTUALIZACIÓN")

    todas = []
    enlaces_vistos = set()

    noticias_insonoro = leer_insonoro()
    todas.extend(noticias_insonoro)

    for nombre, url in FUENTES_RSS:
        noticias = leer_rss(nombre, url)
        todas.extend(noticias)

    resultado = []

    for noticia in todas:
        enlace = noticia["url"]

        if enlace not in enlaces_vistos:
            enlaces_vistos.add(enlace)
            resultado.append(noticia)

    resultado.sort(
        key=lambda noticia: noticia["fecha"],
        reverse=True
    )

    guardar_json("noticias.json", resultado)

    # Se mantienen estos archivos para la web.
    if not os.path.exists(
        os.path.join(CARPETA_DATA, "conciertos.json")
    ):
        guardar_json("conciertos.json", [])

    if not os.path.exists(
        os.path.join(CARPETA_DATA, "videos.json")
    ):
        guardar_json("videos.json", [])

    print("Actualización terminada.")
    print("Total de noticias:", len(resultado))


main()
