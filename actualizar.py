import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

FUENTES = [
    "https://www.insonoro.com/"
]

CARPETA_DATA = "data"


def obtener_noticias():
    noticias = []
    vistos = set()

    for url in FUENTES:
        try:
            respuesta = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20
            )
            respuesta.raise_for_status()

            soup = BeautifulSoup(
                respuesta.text,
                "html.parser"
            )

            for enlace in soup.find_all("a", href=True):
                titulo = enlace.get_text(" ", strip=True)
                destino = enlace["href"]

                if not titulo or len(titulo) < 15:
                    continue

                if destino.startswith("/"):
                    destino = url.rstrip("/") + destino

                if not destino.startswith("http"):
                    continue

                if destino in vistos:
                    continue

                vistos.add(destino)

                noticias.append({
                    "titulo": titulo,
                    "url": destino,
                    "fuente": "Insonoro",
                    "fecha": datetime.now(
                        timezone.utc
                    ).strftime("%Y-%m-%d")
                })

                if len(noticias) >= 30:
                    break

        except Exception as error:
            print(f"Error leyendo {url}: {error}")

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
    print("Iniciando Radikal Sonoro...")

    noticias = obtener_noticias()

    guardar_json("noticias.json", noticias)
    guardar_json("conciertos.json", [])
    guardar_json("videos.json", [])

    print("Actualización terminada.")
    print("Noticias encontradas:", len(noticias))


main()
