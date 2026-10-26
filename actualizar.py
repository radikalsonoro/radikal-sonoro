import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
import re
import os

FUENTES = {
    "noticias": [
        ("Punk", "punk rock"),
        ("Hardcore", "hardcore punk"),
        ("Ska", "ska music"),
        ("Metal", "metal music"),
        ("Underground", "underground music Spain"),
    ],
    "conciertos": [
        ("Punk", "conciertos punk España"),
        ("Hardcore", "conciertos hardcore España"),
        ("Ska", "conciertos ska España"),
        ("Metal", "conciertos metal España"),
    ],
}


def obtener_rss(consulta):
    parametros = urllib.parse.urlencode({
        "q": consulta,
        "hl": "es",
        "gl": "ES",
        "ceid": "ES:es",
    })

    url = "https://news.google.com/rss/search?" + parametros

    peticion = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(peticion, timeout=20) as respuesta:
        return ET.fromstring(respuesta.read())


def limpiar(texto):
    texto = re.sub(r"<[^>]+>", " ", texto or "")
    return re.sub(r"\s+", " ", unescape(texto)).strip()


def recopilar(tipo):
    resultados = []
    vistos = set()

    for categoria, consulta in FUENTES[tipo]:
        try:
            raiz = obtener_rss(consulta)

            for item in raiz.findall(".//item"):
                titulo = limpiar(item.findtext("title"))
                enlace = limpiar(item.findtext("link"))
                resumen = limpiar(item.findtext("description"))
                fecha = limpiar(item.findtext("pubDate"))

                if not titulo or not enlace or enlace in vistos:
                    continue

                vistos.add(enlace)

                try:
                    fecha = parsedate_to_datetime(fecha).isoformat()
                except Exception:
                    fecha = ""

                resultados.append({
                    "categoria": categoria,
                    "titulo": titulo,
                    "enlace": enlace,
                    "resumen": resumen[:300],
                    "fecha": fecha,
                })

        except Exception as error:
            print(f"Error en {categoria}: {error}")

    resultados.sort(
        key=lambda noticia: noticia["fecha"],
        reverse=True
    )

    return resultados[:50]


os.makedirs("data", exist_ok=True)

for tipo in ("noticias", "conciertos"):
    datos = {
        "actualizado": datetime.now(timezone.utc).isoformat(),
        "elementos": recopilar(tipo),
    }

    with open(
        f"data/{tipo}.json",
        "w",
        encoding="utf-8"
    ) as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)

    print(f"{tipo}: {len(datos['elementos'])} resultados")
