import os

from sqlalchemy import create_engine, text


_database_url = os.getenv("DATABASE_URL")
if _database_url and _database_url.startswith("postgres://"):
    _database_url = "postgresql+psycopg://" + _database_url.removeprefix("postgres://")

engine = create_engine(_database_url, pool_pre_ping=True) if _database_url else None


def usar_cloud_sql() -> bool:
    return engine is not None


def inicializar_base_datos() -> None:
    if engine is None:
        return

    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS pasaportes (
                id VARCHAR(20) PRIMARY KEY,
                tipo_ruta VARCHAR(30) NOT NULL,
                ruta_nombre VARCHAR(100) NOT NULL,
                municipio VARCHAR(100) NOT NULL,
                personas_hogar INTEGER,
                actividad_economica VARCHAR(150),
                danos JSONB NOT NULL DEFAULT '[]'::jsonb,
                necesidades JSONB NOT NULL DEFAULT '[]'::jsonb,
                puede_operar BOOLEAN,
                urgencia VARCHAR(30),
                que_hacer_primero TEXT NOT NULL,
                ruta JSONB NOT NULL DEFAULT '[]'::jsonb,
                progreso INTEGER NOT NULL DEFAULT 0,
                estado VARCHAR(50) NOT NULL DEFAULT 'En recuperación',
                ayudas JSONB NOT NULL DEFAULT '[]'::jsonb,
                prioridad_nivel VARCHAR(20) NOT NULL DEFAULT 'amarillo',
                prioridad_etiqueta VARCHAR(50) NOT NULL DEFAULT 'Media',
                confianza_nivel VARCHAR(20) NOT NULL DEFAULT 'amarillo',
                confianza_etiqueta VARCHAR(80) NOT NULL DEFAULT 'Requiere validación',
                creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                actualizado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        for columna, tipo in (
            ("personas_hogar", "INTEGER"),
            ("actividad_economica", "VARCHAR(150)"),
            ("danos", "JSONB NOT NULL DEFAULT '[]'::jsonb"),
            ("necesidades", "JSONB NOT NULL DEFAULT '[]'::jsonb"),
            ("puede_operar", "BOOLEAN"),
            ("urgencia", "VARCHAR(30)"),
            ("ruta", "JSONB NOT NULL DEFAULT '[]'::jsonb"),
            ("ayudas", "JSONB NOT NULL DEFAULT '[]'::jsonb"),
            ("prioridad_nivel", "VARCHAR(20) NOT NULL DEFAULT 'amarillo'"),
            ("prioridad_etiqueta", "VARCHAR(50) NOT NULL DEFAULT 'Media'"),
            ("confianza_nivel", "VARCHAR(20) NOT NULL DEFAULT 'amarillo'"),
            ("confianza_etiqueta", "VARCHAR(80) NOT NULL DEFAULT 'Requiere validación'"),
            ("creado_en", "TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP"),
            ("actualizado_en", "TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP"),
        ):
            connection.execute(text(
                f"ALTER TABLE pasaportes ADD COLUMN IF NOT EXISTS {columna} {tipo}"
            ))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS acciones_ruta (
                id BIGSERIAL PRIMARY KEY,
                pasaporte_id VARCHAR(20) NOT NULL REFERENCES pasaportes(id) ON DELETE CASCADE,
                numero INTEGER NOT NULL,
                completada BOOLEAN NOT NULL DEFAULT FALSE,
                completada_en TIMESTAMPTZ,
                UNIQUE (pasaporte_id, numero)
            )
        """))
        connection.execute(text("""
            ALTER TABLE acciones_ruta
            ADD COLUMN IF NOT EXISTS descripcion TEXT NOT NULL DEFAULT ''
        """))


def cerrar_base_datos() -> None:
    if engine is not None:
        engine.dispose()