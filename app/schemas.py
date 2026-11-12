"""Response models for the tree identification API."""

from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class _Lenient(BaseModel):
    """Ignores unknown keys and treats `null` values as "use the default"."""

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def _drop_nulls(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if v is not None}
        return data


class Alternative(_Lenient):
    nume_popular: str = ""
    nume_latin: str = ""
    cum_le_deosebesti: str = ""


class Aspect(_Lenient):
    frunze_sau_ace: str = ""
    scoarta: str = ""
    flori: str = ""
    fructe_seminte: str = ""
    talie_forma: str = ""


class Utilizari(_Lenient):
    fruct: str = ""
    frunze: str = ""
    scoarta: str = ""
    lemn: str = ""
    altele: str = ""


class Identification(_Lenient):
    identificabil: bool
    mesaj: str = ""
    ce_se_vede: str = ""
    nume_popular: str = ""
    nume_latin: str = ""
    alte_nume: str = ""
    familie: str = ""
    categorie: str = ""
    incredere: str = ""
    de_ce: str = ""
    alternative: list[Alternative] = []
    rezumat: str = ""
    aspect: Aspect = Aspect()
    habitat: str = ""
    in_romania: str = ""
    utilizari: Utilizari = Utilizari()
    toxicitate: str = ""
    curiozitati: list[str] = []
    sfat_poza: str = ""
