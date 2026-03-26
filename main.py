import os
import re
import time
import json
import shutil
import logging
import queue
import threading
from threading import Lock
import sys
import glob
import datetime as dt
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import pandas as pd
import urllib.parse
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from utils import enviar_correo
from notification_manager import NotificationManager, integrate_with_archive_file

notification_manager = NotificationManager("notification_config.json")

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    WATCHDOG_AVAILABLE = True
except Exception:
    WATCHDOG_AVAILABLE = False

load_dotenv()


# Config
@dataclass
class TargetConfig:
    """Configuración para un destino específico de base de datos
    Soporta archivos XLSX y CSV
    """

    server: str
    database: str
    schema: str
    table: str
    username: str = ""
    password: str = ""
    encrypt: str = "yes"
    trust_cert: str = "yes"
    driver: str = "ODBC Driver 17 for SQL Server"
    merge_procedure: str = ""
    merge_procedure_params: Optional[str] = None
    expected_columns: List[str] = None

    # Parámetros comunes
    skip_rows: int = 0
    preserve_text: bool = False

    # Parámetros xlsx
    file_type: str = "xlsx"
    sheet_name: Optional[str] = None
    header_row: Optional[int] = None
    use_cols: Optional[List[str]] = None

    # Parámetros csv
    csv_delimiter: str = ","
    csv_encoding: str = "utf-8"
    csv_has_header: bool = True
    csv_column_names: Optional[List[str]] = None
    csv_quotechar: str = '"'
    csv_decimal: str = "."
    csv_thousands: Optional[str] = None

    def __post_init__(self):
        if self.expected_columns is None:
            self.expected_columns = []

        self.file_type = self.file_type.lower()

        if self.file_type == "xlsx" and not self.sheet_name:
            raise ValueError("XLSX requiere especificar hoja de carga")

        if (
            self.file_type == "csv"
            and not self.csv_has_header
            and not self.csv_column_names
        ):
            raise ValueError("CSV sin encabezado requiere 'csv_column_names'")


@dataclass
class RouteRule:
    """Regla de enrutamiento basada en el nombre del archivo"""

    pattern: str
    target_config: TargetConfig
    description: str = ""
    generica: bool = True

    def extract_params(self, filename: str) -> dict:
        """Extrae parámetros del nombre del archivo usando grupos en el regex"""
        match = re.match(self.pattern, os.path.basename(filename), re.IGNORECASE)
        if match and match.groups():
            return {"param1": match.group(1)}
        return {}

    def matches(self, filename: str) -> bool:
        """Verifica si el archivo coincide con el patrón"""
        return bool(re.match(self.pattern, os.path.basename(filename), re.IGNORECASE))


@dataclass
class DirectoryConfig:
    """Configuración para un directorio a monitorear"""

    path: str
    archive_dir: str
    failed_dir: str
    route_rules: List[RouteRule]

    def __post_init__(self):
        # Crear directorios si no existen
        os.makedirs(self.path, exist_ok=True)
        os.makedirs(self.archive_dir, exist_ok=True)
        os.makedirs(self.failed_dir, exist_ok=True)


class ETLConfig:
    """Gestor de configuración del sistema ETL"""

    def __init__(self, config_file: str = None):
        self.config_file = config_file or os.getenv(
            "ETL_CONFIG_FILE", "etl_config.json"
        )
        self.directories: List[DirectoryConfig] = []
        self.engines_cache: Dict[str, Engine] = {}
        self.load_config()

    def load_config(self):
        """Carga la configuración desde archivo JSON o variables de entorno"""
        if os.path.exists(self.config_file):
            self._load_from_json()
        else:
            self._load_from_env()

    def _load_from_json(self):
        """Carga configuración desde archivo JSON"""
        with open(self.config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        for dir_config in config.get("directories", []):
            route_rules = []
            for rule in dir_config.get("route_rules", []):
                target = rule["target"]

                # Parámetros base
                target_config = TargetConfig(
                    server=target["server"],
                    database=target["database"],
                    schema=target.get("schema", "dbo"),
                    table=target["table"],
                    username=target.get("username", ""),
                    password=target.get("password", ""),
                    encrypt=target.get("encrypt", "yes"),
                    trust_cert=target.get("trust_cert", "yes"),
                    driver=target.get("driver", "ODBC Driver 17 for SQL Server"),
                    merge_procedure=target.get("merge_procedure", ""),
                    expected_columns=target.get("expected_columns", []),
                    skip_rows=target.get("skip_rows", 0),
                    preserve_text=target.get("preserve_text", False),
                    # Tipo archivo
                    file_type=target.get("file_type", "xlsx"),
                    # .xlsx
                    sheet_name=target.get("sheet_name"),
                    header_row=target.get("header_row"),
                    use_cols=target.get("use_cols"),
                    # .csv
                    csv_delimiter=target.get("csv_delimiter", ","),
                    csv_encoding=target.get("csv_encoding", "utf-8"),
                    csv_has_header=target.get("csv_has_header", True),
                    csv_column_names=target.get("csv_column_names"),
                    csv_quotechar=target.get("csv_quotechar", '"'),
                    csv_decimal=target.get("csv_decimal", "."),
                    csv_thousands=target.get("csv_thousands"),
                )

                route_rules.append(
                    RouteRule(
                        pattern=rule["pattern"],
                        target_config=target_config,
                        description=rule.get("description", ""),
                        generica=target.get("generica", True),
                    )
                )

            self.directories.append(
                DirectoryConfig(
                    path=dir_config["path"],
                    archive_dir=dir_config.get(
                        "archive_dir", os.path.join(dir_config["path"], "_archive")
                    ),
                    failed_dir=dir_config.get(
                        "failed_dir", os.path.join(dir_config["path"], "_failed")
                    ),
                    route_rules=route_rules,
                )
            )

    def _load_from_env(self):
        """Carga configuración desde variables de entorno"""
        # Config por defecto
        watch_dir = os.getenv("WATCH_DIR", ".")

        rules = []

        if os.getenv("SQL_SERVER_CURSOS"):
            rules.append(
                RouteRule(
                    pattern=r".*cursos.*\.xlsx$",
                    target_config=TargetConfig(
                        server=os.getenv(
                            "SQL_SERVER_CURSOS", os.getenv("SQL_SERVER", "")
                        ),
                        database="TH_LABS",
                        schema="dbo",
                        table="stg_excel_load_cursos",
                        username=os.getenv(
                            "SQL_USERNAME_CURSOS", os.getenv("SQL_USERNAME", "")
                        ),
                        password=os.getenv(
                            "SQL_PASSWORD_CURSOS", os.getenv("SQL_PASSWORD", "")
                        ),
                    ),
                    description="Archivos cursos hacia base TH_LABS",
                )
            )

        if os.getenv("SQL_SERVER_CENT"):
            rules.append(
                RouteRule(
                    pattern=r".*cent.*\.xlsx$",
                    target_config=TargetConfig(
                        server=os.getenv(
                            "SQL_SERVER_CENT", os.getenv("SQL_SERVER", "")
                        ),
                        database="TH_LABS",
                        schema="dbo",
                        table="stg_excel_load_cent",
                        username=os.getenv(
                            "SQL_USERNAME_CENT", os.getenv("SQL_USERNAME", "")
                        ),
                        password=os.getenv(
                            "SQL_PASSWORD_CENT", os.getenv("SQL_PASSWORD", "")
                        ),
                    ),
                    description="Archivos cent hacia base TH_LABS",
                )
            )

        # Reglas por defecto
        if os.getenv("SQL_SERVER"):
            rules.append(
                RouteRule(
                    pattern=r".*\.xlsx$",
                    target_config=TargetConfig(
                        server=os.getenv("SQL_SERVER", ""),
                        database=os.getenv("SQL_DATABASE", ""),
                        schema=os.getenv("SQL_SCHEMA", "dbo"),
                        table=os.getenv("SQL_STAGING_TABLE", "stg_excel_load"),
                        username=os.getenv("SQL_USERNAME", ""),
                        password=os.getenv("SQL_PASSWORD", ""),
                        encrypt=os.getenv("SQL_ENCRYPT", "yes"),
                        trust_cert=os.getenv("SQL_TRUST_SERVER_CERTIFICATE", "yes"),
                        driver=os.getenv("SQL_DRIVER", "ODBC Driver 17 for SQL Server"),
                        merge_procedure=os.getenv("MERGE_PROCEDURE", ""),
                        expected_columns=[
                            c.strip()
                            for c in os.getenv("EXPECTED_COLUMNS", "").split(",")
                            if c.strip()
                        ],
                        sheet_name=os.getenv("SHEET_NAME") or None,
                    ),
                    description="Regla por defecto",
                )
            )

        if rules:
            self.directories.append(
                DirectoryConfig(
                    path=watch_dir,
                    archive_dir=os.getenv(
                        "ARCHIVE_DIR", os.path.join(watch_dir, "_archive")
                    ),
                    failed_dir=os.getenv(
                        "FAILED_DIR", os.path.join(watch_dir, "_failed")
                    ),
                    route_rules=rules,
                )
            )

    def get_engine_key(self, config: TargetConfig) -> str:
        """Genera una clave única para el cache de engines"""
        return f"{config.server}|{config.database}|{config.username}"

    def get_engine(self, config: TargetConfig) -> Engine:
        """Obtiene o crea un engine de SQLAlchemy para la configuración dada"""
        key = self.get_engine_key(config)

        if key not in self.engines_cache:
            self.engines_cache[key] = self._create_engine(config)

        return self.engines_cache[key]

    def _create_engine(self, config: TargetConfig) -> Engine:
        """Crea engine de SQLAlchemy"""
        parts = [
            f"DRIVER={{{config.driver}}}",
            f"SERVER={{{config.server}}}",
            f"DATABASE={config.database}",
            f"Encrypt={config.encrypt}",
            f"TrustServerCertificate={config.trust_cert}",
            "Timeout=30",
        ]

        if config.username and config.password:
            parts.append(f"UID={config.username}")
            parts.append(f"PWD={config.password}")
        else:
            parts.append("Trusted_Connection=yes")

        odbc_str = ";".join(parts).replace(f"{{{config.driver}}}", config.driver)
        odbc_enc = urllib.parse.quote_plus(odbc_str)

        return create_engine(
            f"mssql+pyodbc:///?odbc_connect={odbc_enc}",
            fast_executemany=True,
            pool_pre_ping=True,
        )

    def dispose_engines(self):
        """Cierra todas las conexiones"""
        for engine in self.engines_cache.values():
            try:
                engine.dispose()
            except Exception:
                pass
        self.engines_cache.clear()


# Config global
RUN_MODE = os.getenv("RUN_MODE", "watch").lower()
# POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
FILE_STABLE_CHECKS = int(os.getenv("FILE_STABLE_CHECKS", "3"))
FILE_STABLE_INTERVAL = float(os.getenv("FILE_STABLE_INTERVAL", "1.0"))
FILE_READY_TIMEOUT = int(os.getenv("FILE_READY_TIMEOUT", "600"))
LOG_DIR = os.getenv("LOG_DIR", ".")
LOG_PATH = os.path.join(LOG_DIR, "main.log")

# Logger
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger("main")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    LOG_PATH, maxBytes=10_000_000, backupCount=5, encoding="utf-8"
)
fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler.setFormatter(fmt)
logger.addHandler(handler)
console = logging.StreamHandler(sys.stdout)
console.setFormatter(fmt)
logger.addHandler(console)


def now_stamp():
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def is_temp_file(filename: str) -> bool:
    """Detecta archivos temporales que deben ser ignorados"""
    base = os.path.basename(filename)

    if base.startswith("~$"):
        return True

    if base.startswith(".~") or base.endswith("~"):
        return True

    if base.startswith("."):
        return True

    return False


def is_processable_file(filename: str) -> bool:
    """
    Verifica si el archivo es procesable por el sistema
    Soporta: .xlsx, .csv
    """
    if is_temp_file(filename):
        return False

    lower_name = filename.lower()
    return lower_name.endswith((".xlsx", ".csv"))


def get_file_type(filename: str) -> Optional[str]:
    """
    Determina el tipo de archivo basado en extensión
    Retorna 'xlsx', 'csv', o None
    """
    lower_name = filename.lower()

    if lower_name.endswith(".xlsx"):
        return "xlsx"
    elif lower_name.endswith(".csv"):
        return "csv"
    else:
        return None


# def is_excel_temp(filename: str) -> bool:
#     # Evitar archivos temporales de Excel (~$Nombre.xlsx)
#     base = os.path.basename(filename)
#     return base.startswith("~$")


def wait_file_ready(path: str) -> bool:
    """Espera a que el archivo deje de crecer (tamaño estable) y exista sin bloquear.
    Devuelve True si está listo, False si excede timeout.
    """
    logger.info(f"Esperando estabilidad de archivo: {path}")
    start = time.time()
    stable_count = 0
    last_size = -1

    while True:
        if not os.path.exists(path):
            # Puede ser una operación de movimiento, esperamos un poco
            if time.time() - start > FILE_READY_TIMEOUT:
                logger.error(f"Timeout esperando archivo (no existe): {path}")
                return False
            time.sleep(FILE_STABLE_INTERVAL)
            continue

        try:
            size = os.path.getsize(path)
        except OSError:
            size = -1

        if size == last_size and size > 0:
            stable_count += 1
            if stable_count >= FILE_STABLE_CHECKS:
                logger.info(f"Archivo estable y listo: {path} (tamaño {size})")
                return True
        else:
            stable_count = 0
            last_size = size

        if time.time() - start > FILE_READY_TIMEOUT:
            logger.error(f"Timeout esperando estabilidad de archivo {path}")
            return False

        time.sleep(FILE_STABLE_INTERVAL)


def archive_file(
    src: str,
    dir_config: DirectoryConfig,
    ok: bool,
    error_msg: str = None,
    target_info: dict = None,
    generica: bool = True,
):
    """Archiva o mueve a carpeta de errores según el resultado con notificaciones"""
    if not os.path.exists(src):
        logger.warning(f"Archivo ya no existe, no se puede mover: {src}")
        return  # Evita error al intentar mover archivo inexistente

    base = os.path.basename(src)
    stamp = now_stamp()

    directory_path = dir_config.path

    if ok:
        dst = os.path.join(dir_config.archive_dir, f"{stamp}__{base}")
        logger.info(f"Archivando OK -> {dst}")
        shutil.move(src, dst)

        notification_manager.send_success_notification(
            filepath=src,
            directory_path=directory_path,
            target_info=target_info,
            generica=generica,
        )

    else:
        dst = os.path.join(dir_config.failed_dir, f"{stamp}__{base}")
        logger.error(f"Moviendo a FAILED -> {dst}")
        shutil.move(src, dst)

        if error_msg:
            # Guarda un .err con el detalle
            err_path = dst + ".err.txt"
            with open(err_path, "w", encoding="utf-8") as f:
                f.write(error_msg)

        notification_manager.send_failure_notification(
            filepath=src,
            directory_path=directory_path,
            error_msg=error_msg or "Error desconocido",
            error_details=error_msg,
        )


def load_file_to_staging(file_path: str, target: TargetConfig, engine: Engine):
    """
    Carga archivo a tabla staging

    Args:
        file_path: Ruta del archivo a procesar
        target: Configuración del destino
        engine: Engine de SQLAlchemy
    """
    logger.info(f"Procesando archivo: {file_path} (tipo={target.file_type})")

    if target.file_type == "xlsx":
        df = _read_excel_file(file_path, target)
    elif target.file_type == "csv":
        df = _read_csv_file(file_path, target)
    else:
        raise ValueError(f"Tipo de archivo no soportado: {target.file_type}")

    # Validaciones
    if target.expected_columns:
        missing = [c for c in target.expected_columns if c not in df.columns]
        if missing:
            raise ValueError(
                f"Columnas faltantes en archivo: {missing}. "
                f"Encontradas: {list(df.columns)}"
            )
        df = df[target.expected_columns]

    # Limpiezas mínimas (opcional)
    df = df.dropna(how="all")
    # Normalizar nombres de columnas y truncar si son muy largos
    df.columns = [str(c).strip()[:128] for c in df.columns]

    df = _prepare_dataframe_for_sql(df)

    full_table = f"{target.database}.{target.schema}.{target.table}"
    total_rows = len(df)
    logger.info(f"Cargando {total_rows:,} filas a {full_table}")

    CHUNK = 50_000
    with engine.begin() as conn:
        conn.exec_driver_sql("SET XACT_ABORT ON; SET LOCK_TIMEOUT 30000;")

        if total_rows == 0:
            logger.info("DataFrame vacío. Nada que cargar.")
            df_empty = pd.DataFrame(columns=df.columns)
            df_empty.to_sql(
                target.table,
                schema=target.schema,
                con=conn,
                if_exists="replace",
                index=False,
            )
        else:
            # Primera carga con replace para crear/limpiar la tabla
            first_chunk = df.iloc[:CHUNK] if total_rows > CHUNK else df
            first_chunk.to_sql(
                target.table,
                schema=target.schema,
                con=conn,
                if_exists="replace",
                index=False,
                # method='multi',
                # chunksize=1000, # Sub-chunks para el INSERT multi-row
            )
            logger.info(f"Primer chunk cargado: {len(first_chunk)} filas")

            # Resto de los chunks con append
            if total_rows > CHUNK:
                for start in range(CHUNK, total_rows, CHUNK):
                    end = min(start + CHUNK, total_rows)
                    df_chunk = df.iloc[start:end]

                    df_chunk.to_sql(
                        target.table,
                        schema=target.schema,
                        con=conn,
                        if_exists="append",
                        index=False,
                        # method='multi',
                        # chunksize=1000,
                    )
                    pct = (end / total_rows) * 100
                    logger.info(
                        f"Chunk {start + 1:,}-{end:,} de {total_rows:,} ({pct:.1f}%)"
                    )

        logger.info("Carga a staging completada")

        if target.merge_procedure:
            if target.merge_procedure_params:
                sql = f"EXEC {target.merge_procedure} @PER_PRO = ?"
                logger.info(f"Ejecutando MERGE con parámetros: {sql}")
                conn.exec_driver_sql(sql, (target.merge_procedure_params,))
            else:
                sql = f"EXEC {target.merge_procedure}"
                logger.info(f"Ejecutando MERGE: {sql}")
                conn.exec_driver_sql(sql)
            logger.info("MERGE ejecutado correctamente.")


def _prepare_dataframe_for_sql(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara el Dataframe para evitar errores con fast_executemany.

    fast_executemany es sensible a:
    - NaN/NaT en columnas datetime
    - Tipos mixtos en columnas
    - Strings muy largos
    """
    df = df.copy()

    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].astype(object).where(df[col].notna(), None)
        elif pd.api.types.is_float_dtype(df[col]):
            df[col] = df[col].astype(object).where(df[col].notna(), None)
        elif df[col].dtype == "object":
            df[col] = df[col].where(df[col].notna(), None)

    return df


def _read_excel_file(file_path: str, target: TargetConfig) -> pd.DataFrame:
    """Lee archivo XLSX con configuración específica"""
    logger.info(f"  → Leyendo XLSX: hoja={target.sheet_name}")

    read_params = {"sheet_name": target.sheet_name, "engine": "openpyxl"}

    if target.skip_rows > 0:
        read_params["skiprows"] = target.skip_rows

    if target.preserve_text:
        read_params["dtype"] = str
        logger.info("  → Modo preserve_text: todas las columnas como texto")

    df = pd.read_excel(file_path, **read_params)
    logger.info(f"  → Leídas {len(df):,} filas, {len(df.columns)} columnas")

    return df


def _read_csv_file(file_path: str, target: TargetConfig) -> pd.DataFrame:
    """Lee archivo CSV con configuración específica"""
    logger.info(
        f"  → Leyendo CSV: delimitador='{target.csv_delimiter}', "
        f"encoding={target.csv_encoding}"
    )

    read_params = {
        "sep": target.csv_delimiter,
        "encoding": target.csv_encoding,
        "quotechar": target.csv_quotechar,
        "decimal": target.csv_decimal,
        "engine": "python",
    }

    if target.csv_has_header:
        read_params["header"] = 0
    else:
        read_params["header"] = None
        if target.csv_column_names:
            read_params["names"] = target.csv_column_names
            logger.info(
                f"  → CSV sin encabezado: usando nombres {target.csv_column_names}"
            )

    if target.skip_rows > 0:
        read_params["skiprows"] = target.skip_rows

    if target.preserve_text:
        read_params["dtype"] = str
        logger.info("  → Modo preserve_text: todas las columnas como texto")

    if target.csv_thousands:
        read_params["thousands"] = target.csv_thousands

    try:
        df = pd.read_csv(file_path, **read_params)
    except UnicodeDecodeError:
        logger.warning(
            f"Error con encoding {target.csv_encoding}, intentando con 'latin-1'"
        )
        read_params["encoding"] = "latin-1"
        df = pd.read_csv(file_path, **read_params)

    logger.info(f"  → Leídas {len(df):,} filas, {len(df.columns)} columnas")

    return df


def find_matching_rule(
    filename: str, dir_config: DirectoryConfig
) -> Optional[RouteRule]:
    """Encuentra la primera regla que coincide con el nombre del archivo"""
    for rule in dir_config.route_rules:
        if rule.matches(filename):
            logger.info(
                f"Archivo '{filename}' coincide con regla: {rule.description or rule.pattern}"
            )

            return rule
    return None


def process_file(file_path: str, dir_config: DirectoryConfig, etl_config: ETLConfig):
    """
    Procesa un archivo individual según las reglas de enrutamiento
    """
    if is_temp_file(file_path):
        logger.info(f"Ignorando archivo temporal: {file_path}")
        return

    if not is_processable_file(file_path):
        logger.info(f"Ignorando archivo no procesable: {file_path}")
        return

    if not os.path.exists(file_path):
        logger.warning(f"⚠ Archivo ya no existe: {file_path}")
        return

    # Buscar regla de enrutamiento
    rule = find_matching_rule(file_path, dir_config)

    if not rule:
        logger.warning(f"⚠ No se encontró regla de enrutamiento para: {file_path}")
        archive_file(
            file_path,
            dir_config,
            ok=False,
            error_msg="No se encontró ruta de enrutamiento",
        )
        return

    detected_type = get_file_type(file_path)
    if detected_type != rule.target_config.file_type:
        logger.warning(
            f"⚠ Tipo de archivo detectado ({detected_type}) no coincide "
            f"con configuración ({rule.target_config.file_type})"
        )
        archive_file(
            file_path,
            dir_config,
            ok=False,
            error_msg=f"Tipo de archivo incompatible: esperado {rule.target_config.file_type}, "
            f"encontrado {detected_type}",
        )
        return

    # Extraer parámetros del nombre si el patrón tiene grupos
    params = rule.extract_params(file_path)
    if params.get("param1"):
        rule.target_config.merge_procedure_params = params["param1"]
        logger.info(f"  -> Parámetro extraído: {params['param1']}")

    # Log de procesamiento
    logger.info(f"{'=' * 60}")
    logger.info(f"📄 Procesando: {os.path.basename(file_path)}")
    logger.info(f"📂 Directorio: {dir_config.path}")
    logger.info(f"📋 Tipo: {rule.target_config.file_type.upper()}")
    logger.info(
        f"🗄️ Destino: {rule.target_config.server}/{rule.target_config.database}"
        f".{rule.target_config.schema}.{rule.target_config.table}"
    )
    logger.info(f"{'=' * 60}")

    if not wait_file_ready(file_path):
        archive_file(
            file_path,
            dir_config,
            ok=False,
            error_msg="Timeout esperando estabilidad del archivo",
        )
        return

    try:
        engine = etl_config.get_engine(rule.target_config)

        if rule.target_config.file_type == "xlsx":
            df_preview = pd.read_excel(
                file_path, sheet_name=rule.target_config.sheet_name, nrows=0
            )
            df_count = pd.read_excel(
                file_path, sheet_name=rule.target_config.sheet_name
            )
            rows_loaded = len(df_count)
        else:
            df_count = pd.read_csv(
                file_path,
                sep=rule.target_config.csv_delimiter,
                encoding=rule.target_config.csv_encoding,
                nrows=None,
            )
            rows_loaded = len(df_count)

        load_file_to_staging(file_path, rule.target_config, engine)

        target_info = {
            "server": rule.target_config.server,
            "database": rule.target_config.database,
            "schema": rule.target_config.schema,
            "table": rule.target_config.table,
            "rows_loaded": rows_loaded,
            "file_type": rule.target_config.file_type.upper(),
            "generica": rule.generica,
        }

        archive_file(
            file_path,
            dir_config,
            ok=True,
            target_info=target_info,
            generica=rule.generica,
        )

    except Exception as e:
        error_msg = f"Error procesando {file_path}:\n{str(e)}"
        logger.exception(error_msg)
        archive_file(file_path, dir_config, ok=False, error_msg=str(e))


class FileProcessorQueue:
    """Cola de procesamiento secuencial para evitar bloqueos de BD"""

    def __init__(self):
        self.file_queue = queue.Queue()
        self.processing_lock = Lock()
        self.worker_thread = None
        self.stop_processing = False

    def add_file(self, filepath, dir_config, etl_config):
        """Agrega archivo a la cola"""
        self.file_queue.put((filepath, dir_config, etl_config))
        logger.info(
            f"Archivo agregado a cola: {filepath} (tamaño cola: {self.file_queue.qsize()})"
        )

    def process_queue(self):
        """Procesar archivos de la cola secuencialmente"""
        while not self.stop_processing:
            try:
                if not self.file_queue.empty():
                    filepath, dir_config, etl_config = self.file_queue.get(timeout=1)
                    with self.processing_lock:
                        logger.info(f"Procesando de la cola: {filepath}")
                        process_file(filepath, dir_config, etl_config)
                    self.file_queue.task_done()
                else:
                    time.sleep(1)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error en procesamiento de cola: {e}")

    def start_worker(self):
        """Inicia el worker thread"""
        if not self.worker_thread or not self.worker_thread.is_alive():
            self.worker_thread = threading.Thread(
                target=self.process_queue, daemon=True
            )
            self.worker_thread.start()
            logger.info("Worker de procesamiento iniciado")

    def stop(self):
        """Detiene el procesamiento"""
        self.stop_processing = True
        if self.worker_thread:
            self.worker_thread.join(timeout=5)


# Instancia global de la cola
file_processor = FileProcessorQueue()


class MultiDirectoryHandler(FileSystemEventHandler):
    """Handler para múltiples directorios con reglas de enrutamiento"""

    def __init__(self, dir_config: DirectoryConfig, etl_config: ETLConfig):
        super().__init__()
        self.dir_config = dir_config
        self.etl_config = etl_config

    def _should_process(self, path: str) -> bool:
        """Determina si el archivo debe ser procesado"""
        return is_processable_file(path)

    def _queue_file(self, path: str):
        """Agrega archivos a la cola de procesamiento"""
        if self._should_process(path):
            logger.info(f"➕ Agregando a cola: {os.path.basename(path)}")
            file_processor.add_file(path, self.dir_config, self.etl_config)
        else:
            logger.debug(f"⊘ Ignorando: {os.path.basename(path)}")

    def on_created(self, event):
        if event.is_directory:
            return
        self._queue_file(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        self._queue_file(event.dest_path)


def run_watch(etl_config: ETLConfig):
    """Modo WATCH usando watchdog para monitorear cambios"""
    if not WATCHDOG_AVAILABLE:
        logger.error("Watchdog no disponible.")
        sys.exit(2)

    logger.info("*** MODO WATCH ***")
    observers = []

    for dir_config in etl_config.directories:
        logger.info(f"Monitoreando: {dir_config.path}")
        observer = Observer()
        handler = MultiDirectoryHandler(dir_config, etl_config)
        observer.schedule(handler, dir_config.path, recursive=False)
        observer.start()
        observers.append(observer)

    file_processor.start_worker()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Detenido por usuario.")
    finally:
        logger.info("Finalizando observer...")
        file_processor.stop()
        for observer in observers:
            try:
                observer.stop()
            except Exception:
                pass
            try:
                observer.join(timeout=5)
            except Exception:
                pass
        etl_config.dispose_engines()


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Sistema ETL Excel -> SQL Server (Multi-directorio)")
    logger.info("=" * 60)

    etl_config = ETLConfig()

    notification_manager = NotificationManager("notification_config.json")

    notification_manager.send_system_alert(
        f"Sistema ETL iniciado en modo {RUN_MODE.upper()}"
    )

    if not etl_config.directories:
        logger.error("No se configuraron directorios para monitorear.")
        logger.info(
            "Tip: Crea un archivo etl_config.json o configura las variables de entorno."
        )

        notification_manager.send_system_alert(
            "Sistema ETL no pudo iniciar - No hay directorios configurados"
        )

        sys.exit(1)

    logger.info(f"Configurados {len(etl_config.directories)} directorio(s)")
    for dir_config in etl_config.directories:
        logger.info(f"  - {dir_config.path}: {len(dir_config.route_rules)} reglas")

    try:
        if RUN_MODE == "watch":
            run_watch(etl_config)
    except Exception as e:
        logger.exception(f"Error fatal: {e}")

        notification_manager.send_system_alert("Error fatal en sistema ETL", error=e)

        sys.exit(1)
    finally:
        etl_config.dispose_engines()


# === CALIDAD DE DATOS ===

"""
Completitud: Evalúa si todos los datos necesarios están presentes. Un dato está completo si no falta ningún valor requerido para su propósito. Por ejemplo, un registro de empleado sin fecha de ingreso estaría incompleto.

Validez: Se refiere a si los datos cumplen con las reglas de negocio o formatos esperados. Por ejemplo, una fecha de nacimiento no puede ser posterior a la fecha actual, o un código postal debe tener un formato específico.

Unicidad: Garantiza que no existan duplicados donde no deberían. Por ejemplo, un número de identificación único no debe repetirse en la base de datos.

Integridad: Evalúa la relación lógica entre datos. Por ejemplo, si un registro de ventas hace referencia a un cliente, ese cliente debe existir en la tabla correspondiente. La integridad asegura que las conexiones entre entidades estén bien definidas y mantenidas.

Precisión: Mide qué tan correctamente los datos reflejan la realidad. Por ejemplo, si el salario registrado de un empleado es 1.000.000 CLP pero en realidad gana 900.000 CLP, hay un problema de precisión.

Coherencia: Se refiere a la uniformidad de los datos entre diferentes sistemas o dentro del mismo sistema. Por ejemplo, si en un sistema el estado de un cliente es “activo” y en otro “inactivo”, hay una incoherencia.

Disponibilidad: Evalúa si los datos están accesibles cuando se necesitan. Esto incluye tanto la disponibilidad técnica (el sistema funciona) como la disponibilidad lógica (los datos están cargados y actualizados).

Representación: Se refiere a cómo se presentan los datos: si están bien estructurados, etiquetados y documentados para facilitar su comprensión y uso. Una buena representación incluye metadatos claros, formatos estandarizados y definiciones consistentes.
"""
