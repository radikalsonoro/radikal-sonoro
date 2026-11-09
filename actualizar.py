import os
import json
import re
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin

CARPETA_DATA = "data"
URL_TRINCHERA = "https://primeralineavkbar.com/index.php/trinchera/"
CABECERAS = {"User-Agent": "Mozilla/5.0 RadikalSonoro/2.0"}

FUENTES_RSS = [
    ("MariskalRock", "https://mariskalrock.com/feed/"),
    ("Metal Injection", "https://metalinjection.net/feed/"),
    ("Dying Scene", "https://dyingscene.com/feed/"),
    ("IDIOTEQ", "https://idioteq.com/feed/"),
]

PALABRAS_CLAVE = [
    "punk", "hardcore", "ska", "oi!", "oi ", "street punk", "crust",
    "d-beat", "anarcho", "post-punk", "punk rock", "metal", "heavy metal",
    "thrash", "death metal", "black metal", "grindcore", "metalcore",
    "powerviolence", "grunge", "underground", "independent",
    "independiente", "festival", "concierto", "gira", "banda", "bandas",
    "disco", "álbum", "album", "single", "ep ", "sello", "hardcore punk"
]

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12
}

def fecha_actual():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def convertir_fecha(valor):
    if not valor:
        return fecha_actual()
    try:
        return parsedate_to_datetime(valor).strftime("%Y-%m-%d")
    except Exception:
        return fecha_actual()

def es_relevante(titulo, descripcion=""):
    texto = (titulo + " " + descripcion).lower()
    return any(palabra in texto for palabra in PALABRAS_CLAVE)

def leer_rss(nombre, url):
    noticias = []
    try:
        respuesta = requests.get(url, headers=CABECERAS, timeout=25)
        respuesta.raise_for_status()
        raiz = ET.fromstring(respuesta.content)
        elementos = raiz.findall(".//item")
        if not elementos:
            elementos = raiz.findall(".//{http://www.w3.org/2005/Atom}entry")
        for item in elementos:
            titulo = item.findtext("title")
            if titulo is None:
                el = item.find("{http://www.w3.org/2005/Atom}title")
                titulo = el.text if el is not None else ""
            enlace = item.findtext("link")
            if not enlace:
                el = item.find("{http://www.w3.org/2005/Atom}link")
                enlace = el.attrib.get("href", "") if el is not None else ""
            descripcion = item.findtext("description") or item.findtext(
                "{http://www.w3.org/2005/Atom}summary") or ""
            fecha = item.findtext("pubDate") or item.findtext(
                "{http://www.w3.org/2005/Atom}published") or item.findtext(
                "{http://www.w3.org/2005/Atom}updated")
            if titulo and enlace and es_relevante(titulo, descripcion):
                noticias.append({
                    "titulo": titulo.strip(),
                    "url": urljoin(url, enlace),
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
        respuesta = requests.get(url, headers=CABECERAS, timeout=25)
        respuesta.raise_for_status()
        soup = BeautifulSoup(respuesta.text, "html.parser")
        vistos = set()
        for enlace in soup.find_all("a", href=True):
            titulo = enlace.get_text(" ", strip=True)
            destino = urljoin(url, enlace["href"])
            if len(titulo) < 15 or destino in vistos:
                continue
            vistos.add(destino)
            if es_relevante(titulo):
                noticias.append({
                    "titulo": titulo, "url": destino,
                    "fuente": "Insonoro", "fecha": fecha_actual()
                })
            if len(noticias) >= 30:
                break
        print(f"Insonoro: {len(noticias)} noticias")
    except Exception as error:
        print(f"Error leyendo Insonoro: {error}")
    return noticias

def fecha_evento_trinchera(texto):
    coincidencia = re.search(
        r"\b(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|"
        r"julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)\b",
        texto.lower()
    )
    if not coincidencia:
        return None
    dia = int(coincidencia.group(1))
    mes = MESES[coincidencia.group(2)]
    ahora = datetime.now()
    anio = ahora.year
    try:
        fecha = datetime(anio, mes, dia)
        if fecha.date() < ahora.date() and (ahora.date() - fecha.date()).days > 60:
            fecha = datetime(anio + 1, mes, dia)
        return fecha.strftime("%Y-%m-%d")
    except ValueError:
        return None

def leer_trinchera():
    """Lee la agenda oficial de Primera Línea VK Bar y sus carteles originales."""
    eventos = []
    try:
        respuesta = requests.get(URL_TRINCHERA, headers=CABECERAS, timeout=30)
        respuesta.raise_for_status()
        agenda = BeautifulSoup(respuesta.text, "html.parser")
        enlaces = []
        vistos = set()
        for a in agenda.find_all("a", href=True):
            href = urljoin(URL_TRINCHERA, a["href"])
            if re.search(r"/index\.php/20\d{2}/\d{2}/\d{2}/", href) and href not in vistos:
                vistos.add(href)
                enlaces.append((a.get_text(" ", strip=True), href))
        hoy = datetime.now().date()
        for titulo_lista, url_evento in enlaces:
            try:
                detalle_resp = requests.get(url_evento, headers=CABECERAS, timeout=20)
                detalle_resp.raise_for_status()
                detalle = BeautifulSoup(detalle_resp.text, "html.parser")
                texto = detalle.get_text(" ", strip=True)
                fecha = fecha_evento_trinchera(texto)
                if not fecha or datetime.strptime(fecha, "%Y-%m-%d").date() < hoy:
                    continue
                h1 = detalle.find(["h1", "h2"])
                titulo = h1.get_text(" ", strip=True) if h1 else titulo_lista
                titulo = re.sub(r"\s*[–-]\s*Primera linea VK Bar.*$", "", titulo, flags=re.I).strip()
                hora_match = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\s*HORAS\b", texto, re.I)
                hora = f"{hora_match.group(1).zfill(2)}:{hora_match.group(2)}" if hora_match else ""
                imagen = detalle.find("meta", property="og:image")
                cartel = imagen.get("content", "") if imagen else ""
                if not cartel:
                    img = detalle.find("img")
                    cartel = urljoin(url_evento, img.get("src", "")) if img else ""
                eventos.append({
                    "fecha": fecha, "hora": hora, "evento": titulo,
                    "artistas": titulo, "sala": "Primera Línea VK Bar · La Trinchera",
                    "ciudad": "Madrid", "pais": "España", "url": url_evento,
                    "cartel": cartel, "fuente": "Primera Línea VK Bar",
                    "prioridad": 0
                })
            except Exception as error:
                print(f"No se pudo leer evento de La Trinchera ({url_evento}): {error}")
        print(f"La Trinchera: {len(eventos)} próximos conciertos")
    except Exception as error:
        print(f"No se pudo leer la agenda de La Trinchera: {error}")
    return eventos

def guardar_json(nombre, contenido):
    os.makedirs(CARPETA_DATA, exist_ok=True)
    with open(os.path.join(CARPETA_DATA, nombre), "w", encoding="utf-8") as archivo:
        json.dump(contenido, archivo, ensure_ascii=False, indent=2)

def cargar_conciertos_existentes():
    ruta = os.path.join(CARPETA_DATA, "conciertos.json")
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
            return datos if isinstance(datos, list) else []
    except (OSError, json.JSONDecodeError):
        return []

def actualizar_conciertos():
    hoy = datetime.now().date()
    existentes = cargar_conciertos_existentes()
    nuevos = leer_trinchera()
    por_url_fecha = {}
    for evento in existentes + nuevos:
        fecha = evento.get("fecha", "")
        url = evento.get("url", "")
        try:
            if not fecha or datetime.strptime(fecha, "%Y-%m-%d").date() < hoy or not url:
                continue
        except ValueError:
            continue
        es_trinchera = (
            "primeralineavkbar.com" in url
            or "trinchera" in evento.get("sala", "").lower()
        )
        evento["prioridad"] = 0 if es_trinchera else 1
        clave = (fecha, evento.get("evento", "").strip().lower())
        if clave not in por_url_fecha or evento["prioridad"] < por_url_fecha[clave]["prioridad"]:
            por_url_fecha[clave] = evento
    agenda = sorted(
        por_url_fecha.values(),
        key=lambda e: (e.get("prioridad", 1), e.get("fecha", ""), e.get("hora", ""))
    )[:6]
    for evento in agenda:
        evento.pop("prioridad", None)
    guardar_json("conciertos.json", agenda)
    print("Conciertos publicados:", len(agenda))

def main():
    print("RADIKAL SONORO - ACTUALIZACIÓN")
    todas = leer_insonoro()
    for nombre, url in FUENTES_RSS:
        todas.extend(leer_rss(nombre, url))
    resultado = []
    vistos = set()
    for noticia in todas:
        if noticia["url"] not in vistos:
            vistos.add(noticia["url"])
            resultado.append(noticia)
    resultado.sort(key=lambda noticia: noticia["fecha"], reverse=True)
    guardar_json("noticias.json", resultado)
    actualizar_conciertos()
    if not os.path.exists(os.path.join(CARPETA_DATA, "videos.json")):
        guardar_json("videos.json", [])
    print("Actualización terminada. Noticias:", len(resultado))

main()
