from typing import Optional, List, Literal
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON as JSONType
from pydantic import BaseModel, validator

# ------------------------------------------
# Pydantic model pre vstup z UI
# ------------------------------------------
class LeadIn(BaseModel):
    id: Optional[int] = None
    # Základné údaje
    customer_name: str
    # Adresa (pre Google API)
    address: str
    floors: int = 0
    distance_km: float = 0.0
    # Dĺžky segmentov
    length_spod: float = 0.0
    length_spod_vrch: float = 0.0
    length_full: float = 0.0
    material_dvierok: Optional[Literal["laminát", "folia", "akryl", "striekane"]] = None
    material_pracovnej_dosky: Optional[Literal["bez", "drevodekor", "imitacia_kamena", "kompakt", "umely_kamen"]] = None
    has_island: bool = False
    length_island: float = 0.0
    shape: Literal["rovný", "L", "U"] = "rovný"
    # Extra položky
    led_pas: bool = False
    drawer_count: int = 0
    vrchne_otvaranie_typ: Optional[Literal["zlomove", "klasik"]] = None
    vrchne_doors_count: int = 0
    rohovy_typ: bool = False
    potravinova_skrina_typ: Optional[Literal["vysoka", "nizka"]] = None
    potravinove_sufle_typ: Optional[Literal["vysoke", "nizke"]] = None
    sortier: bool = False
    hidden_coffee: bool = False
    zastena: bool = False
    # Zľava
    discount_pct: float = 0.0
    discount_abs: float = 0.0
    extra_desc: str = ""
    extra_price: float = 0.0

    @validator("length_spod", "length_spod_vrch", "length_full", "length_island", allow_reuse=True)
    def lengths_positive(cls, v):
        if v < 0:
            raise ValueError("Dĺžky musia byť nezáporné čísla.")
        return v
    @validator("drawer_count", "vrchne_doors_count", "floors", allow_reuse=True)
    def ints_non_negative(cls, v):
        if v < 0:
            raise ValueError("Počty musia byť nezáporné.")
        return v

# ------------------------------------------
# SQLModel model pre ukladanie do SQLite
# ------------------------------------------
class Lead(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    data: dict = Field(sa_column=Column(JSONType))
    quoted_price: float = Field(nullable=False)
