from typing import Annotated, List, Literal, Union

from pydantic import BaseModel, Field


class DiagnosticoAyudaInmediata(BaseModel):
    tipo_ruta: Literal["ayuda_inmediata"] = "ayuda_inmediata"
    municipio: str
    personas_hogar: int
    necesidad: str
    urgencia: str
    evidencia: str = ""


class DiagnosticoVivienda(BaseModel):
    tipo_ruta: Literal["vivienda"] = "vivienda"
    municipio: str
    tipo_afectacion: List[str]
    habitabilidad: str
    servicios_afectados: List[str]
    evidencia: str = ""


class DiagnosticoIngresos(BaseModel):
    tipo_ruta: Literal["ingresos"] = "ingresos"
    municipio: str
    actividad_economica: str
    danos: List[str]
    puede_operar: bool
    necesidades: List[str]


DiagnosticoRequest = Annotated[
    Union[DiagnosticoAyudaInmediata, DiagnosticoVivienda, DiagnosticoIngresos],
    Field(discriminator="tipo_ruta"),
]
