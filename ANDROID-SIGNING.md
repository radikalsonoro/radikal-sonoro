# Firma permanente de la aplicación Android

La APK de lanzamiento debe firmarse siempre con la misma clave privada. No guardes el archivo JKS ni sus contraseñas en el repositorio.

## Secretos necesarios en GitHub

En el repositorio, abre **Settings → Secrets and variables → Actions → New repository secret** y crea estos cuatro secretos:

- `ANDROID_KEYSTORE_BASE64`: contenido del archivo JKS convertido a Base64, en una sola línea.
- `ANDROID_KEYSTORE_PASSWORD`: contraseña del almacén.
- `ANDROID_KEY_ALIAS`: alias de la clave.
- `ANDROID_KEY_PASSWORD`: contraseña de la clave.

La clave JKS debe ser creada una sola vez y conservarse en un lugar seguro. No generes una clave nueva para cada versión: Android no permitirá actualizar la aplicación instalada si cambia la firma.

## Compilación

Cuando los cuatro secretos estén configurados, ejecuta **Actions → Crear APK firmada de Radikal Sonoro → Run workflow**. El flujo compila la variante release, verifica la firma y publica `radikal-sonoro.apk` en una nueva release.

## Importante sobre Play Protect

Una firma estable evita conflictos de identidad entre actualizaciones, pero no garantiza que Play Protect deje de mostrar advertencias. Google puede seguir mostrando avisos a aplicaciones instaladas fuera de Play Store o bloquear un APK si lo considera potencialmente dañino. No se debe pedir al usuario que desactive Play Protect para instalarlo.
