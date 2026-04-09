"""
manifest.py — Tracking de archivos procesados via SHA-256

El manifest es la pieza central de la estrategia incremental del pipeline.
Evita re-procesar documentos que no cambiaron desde la última ejecución,
lo que ahorra llamadas a la API del LLM y tiempo de ejecución.

Estrategia:
  - Al iniciar el pipeline, se carga el manifest (o se crea uno vacío)
  - Antes de procesar cada archivo, se calcula su SHA-256 y se compara
    con el valor en el manifest
  - Si el hash coincide, el archivo no cambió → se salta
  - Si el hash difiere o no existe → se procesa y se actualiza el manifest
  - Al finalizar el pipeline, se guarda el manifest actualizado

El manifest se guarda en data/manifest.json y se incluye en los commits
automáticos del pipeline para mantener consistencia entre ejecuciones.

Este módulo es completamente funcional (no un placeholder).
"""

import hashlib
import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

# Versión del schema del manifest — incrementar si cambia la estructura
MANIFEST_VERSION = 1

# Schema vacío para inicializar un manifest nuevo
EMPTY_MANIFEST: dict = {
    "version": MANIFEST_VERSION,
    "last_run": None,
    "files": {},
}


def load_manifest(manifest_path: Path) -> dict:
    """
    Cargar el manifest desde disco.

    Si el archivo no existe (primera ejecución), retorna un manifest vacío.
    Si el archivo existe pero está corrupto, loguea el error y retorna
    un manifest vacío — es mejor reprocesar todo que fallar el pipeline.

    Args:
        manifest_path: Path al archivo manifest.json.

    Returns:
        Dict con la estructura del manifest. Siempre retorna un dict válido,
        nunca lanza excepción.
    """
    if not manifest_path.exists():
        log.info("Manifest no encontrado en %s — creando uno nuevo", manifest_path)
        return dict(EMPTY_MANIFEST)

    try:
        content = manifest_path.read_text(encoding="utf-8")
        data = json.loads(content)

        # Verificar versión del schema
        # Si la versión cambió, retornar vacío para forzar re-procesamiento
        if data.get("version") != MANIFEST_VERSION:
            log.warning(
                "Versión del manifest (%s) difiere de la esperada (%s) — "
                "retornando manifest vacío para re-procesar todo",
                data.get("version"),
                MANIFEST_VERSION,
            )
            return dict(EMPTY_MANIFEST)

        # Asegurar que las keys requeridas existen (robustez ante manifests parciales)
        if "files" not in data:
            data["files"] = {}

        log.info("Manifest cargado: %d archivos registrados", len(data["files"]))
        return data

    except json.JSONDecodeError as exc:
        log.error(
            "Error al parsear manifest.json (%s) — retornando manifest vacío. "
            "Se reprocesarán todos los archivos.",
            exc,
        )
        return dict(EMPTY_MANIFEST)

    except OSError as exc:
        log.error(
            "Error al leer manifest.json (%s) — retornando manifest vacío.",
            exc,
        )
        return dict(EMPTY_MANIFEST)


def save_manifest(manifest_path: Path, manifest: dict) -> None:
    """
    Guardar el manifest en disco.

    Crea el directorio padre si no existe. Escribe de forma atómica:
    primero a un archivo temporal, luego rename para evitar dejar el
    manifest en estado inconsistente si el proceso se interrumpe.

    Args:
        manifest_path: Path donde guardar el manifest.json.
        manifest: Dict con la estructura del manifest a guardar.

    Raises:
        OSError: Si no se puede escribir el archivo (permisos, disco lleno).
    """
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # Escribir a archivo temporal en el mismo directorio para que rename sea atómico
    tmp_path = manifest_path.with_suffix(".json.tmp")

    try:
        tmp_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        # Rename atómico — en Unix, rename() es garantizado atómico
        tmp_path.rename(manifest_path)
        log.info("Manifest guardado en %s (%d archivos)", manifest_path, len(manifest.get("files", {})))

    except Exception:
        # Limpiar el archivo temporal si algo falló
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def compute_file_hash(path: Path) -> str:
    """
    Calcular el SHA-256 de un archivo.

    Lee el archivo en chunks para no cargar archivos grandes enteros en memoria.

    Args:
        path: Path al archivo del que calcular el hash.

    Returns:
        Hash SHA-256 como string hexadecimal en minúsculas.

    Raises:
        OSError: Si el archivo no existe o no se puede leer.
    """
    sha256 = hashlib.sha256()
    chunk_size = 65536  # 64KB chunks

    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)

    return sha256.hexdigest()


def needs_processing(path: Path, manifest: dict, source_key: str | None = None) -> bool:
    """
    Determinar si un archivo necesita ser procesado.

    Un archivo necesita procesamiento si:
    1. No aparece en el manifest (archivo nuevo)
    2. Su SHA-256 difiere del registrado en el manifest (archivo modificado)

    Args:
        path: Path al archivo a verificar.
        manifest: Manifest cargado con load_manifest().
        source_key: Clave estable opcional para la entrada del manifest.

    Returns:
        True si el archivo debe ser procesado, False si puede saltarse.
    """
    path_key = source_key or str(path)
    files = manifest.get("files", {})

    entry = files.get(path_key)
    if entry is None and source_key is not None:
        # Compatibilidad con manifests viejos basados en rutas temporales.
        entry = files.get(str(path))

    if entry is None:
        log.debug("Archivo nuevo (no en manifest): %s", path.name)
        return True

    recorded_hash = entry.get("sha256")
    if not recorded_hash:
        log.debug("Archivo en manifest sin hash registrado: %s", path.name)
        return True

    try:
        current_hash = compute_file_hash(path)
    except OSError as exc:
        log.warning("No se puede calcular hash de %s: %s — se procesará", path.name, exc)
        return True

    if current_hash != recorded_hash:
        log.debug(
            "Archivo modificado (hash cambió): %s\n  anterior: %s\n  actual:   %s",
            path.name,
            recorded_hash[:16] + "...",
            current_hash[:16] + "...",
        )
        return True

    log.debug("Archivo sin cambios (hash igual): %s", path.name)
    return False


def get_manifest_stats(manifest: dict) -> dict:
    """
    Obtener estadísticas del manifest para logging y debugging.

    Args:
        manifest: Manifest cargado con load_manifest().

    Returns:
        Dict con estadísticas: total de archivos, último run, versión.
    """
    files = manifest.get("files", {})
    return {
        "version": manifest.get("version"),
        "total_files": len(files),
        "last_run": manifest.get("last_run"),
    }
