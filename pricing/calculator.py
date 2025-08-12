from typing import Tuple
import math
import requests
from pricing.config import PRICES, SETTINGS
from pricing.models import LeadIn

# 1) Výpočet plôch
def compute_areas(p: LeadIn) -> Tuple[float, float, float]:
    vyska_s = PRICES["vyska_spodneho"]
    vyska_v = PRICES["vyska_vrchneho"]
    vyska_f = PRICES["vyska_full"]
    area_spod = p.length_spod * vyska_s
    area_spod_vrch = p.length_spod_vrch * (vyska_s + vyska_v)
    area_full = p.length_full * vyska_f
    return area_spod, area_spod_vrch, area_full

# 2) Cena korpusu
def calculate_korpus(p: LeadIn) -> float:
    base_price = PRICES["cena_korpus_per_m2"]
    dph_rate = PRICES["dph"]
    marza = PRICES["marza"]
    area_spod, area_spod_vrch, area_full = compute_areas(p)
    total_area = area_spod + area_spod_vrch + area_full
    unit = (base_price * (1 + dph_rate)) * marza
    return unit * total_area

# 3) Cena dvierok
def calculate_dvierka(p: LeadIn) -> float:
    base_price = PRICES["ceny_dvierka"][p.material_dvierok]
    dph_rate = PRICES["dph"]
    marza = PRICES["marza"]
    area_spod, area_spod_vrch, area_full = compute_areas(p)
    door_area = area_spod + area_spod_vrch + area_full
    unit = (base_price * (1 + dph_rate)) * marza
    return unit * door_area

# 4) Cena pracovnej dosky
def calculate_prac_doska(p: LeadIn) -> float:
    if not p.material_pracovnej_dosky or p.material_pracovnej_dosky == "bez":
        return 0.0
    length = p.length_spod + p.length_spod_vrch
    base_price = PRICES["ceny_pracovna_doska"][p.material_pracovnej_dosky]
    marza = PRICES["marza"]
    dph_rate = PRICES["dph"]
    unit = (base_price * (1 + dph_rate)) * marza
    return length * unit

# 4b) Cena zásteny
def calculate_zastena(p: LeadIn) -> float:
    if not p.material_pracovnej_dosky or p.material_pracovnej_dosky == "bez":
        return 0.0
    length = p.length_spod + p.length_spod_vrch
    base_price = PRICES["ceny_pracovna_doska"][p.material_pracovnej_dosky]
    marza = PRICES["marza"]
    dph_rate = PRICES["dph"]
    unit = (base_price * (1 + dph_rate)) * marza
    return length * unit

# 5) Cena ostrovček
def calculate_island(p: LeadIn) -> float:
    if not p.has_island or p.length_island <= 0:
        return 0.0
    unit_k = (PRICES["cena_korpus_per_m2"] * (1 + PRICES["dph"])) * PRICES["marza"]
    area_k = p.length_island * PRICES["vyska_island"]
    c_korpus_island = unit_k * area_k

    base_dv = PRICES["ceny_dvierka"][p.material_dvierok]
    unit_dv = (base_dv * (1 + PRICES["dph"])) * PRICES["marza"]
    c_dv = unit_dv * area_k    # Dve strany ostrova

    base_w = PRICES["ceny_pracovna_doska"][p.material_pracovnej_dosky]
    unit_w = (base_w * (1 + PRICES["dph"])) * PRICES["marza"]
    c_w = p.length_island * unit_w

    return c_korpus_island + c_dv + c_w

# 6) Extra položky
def calculate_extras(p: LeadIn) -> float:
    total = 0.0
    dph_rate = PRICES["dph"]
    marza_kovanie = PRICES["marza_kovanie"]
    # LED pás
    if p.led_pas:
        length = p.length_spod_vrch
        unit_led = (PRICES["led_pas_per_m"] * (1 + dph_rate)) * marza_kovanie
        total += unit_led * length
    # Šuflíky
    if p.drawer_count > 0:
        unit_dr = (PRICES["suflik_price"] * (1 + dph_rate)) * marza_kovanie
        total += unit_dr * p.drawer_count
    # Vrchné otváranie
    if p.vrchne_doors_count > 0 and p.vrchne_otvaranie_typ:
        key = f"vrchne_otvaranie_{p.vrchne_otvaranie_typ}"
        unit_v = (PRICES[key] * (1 + dph_rate)) * marza_kovanie
        total += unit_v * p.vrchne_doors_count
    # Rohový mechanizmus
    if p.rohovy_typ:
        unit_r = (PRICES["rohova_ladvina"] * (1 + dph_rate)) * marza_kovanie
        total += unit_r
    # Potravinová skrina
    if p.potravinova_skrina_typ:
        if p.potravinova_skrina_typ.startswith("vysoka"):
            key = "potravinova_skrina_vysoka"
        else:
            key = "potravinova_skrina_nizka"
        unit_pantry = (PRICES[key] * (1 + dph_rate)) * marza_kovanie
        total += unit_pantry
    # Potravinová skrina
    if p.potravinove_sufle_typ:
        if p.potravinove_sufle_typ.startswith("vysoke"):
            key = "potravinove_sufle_vysoke"
        else:
            key = "potravinove_sufle_nizke"
        unit_pantry = (PRICES[key] * (1 + dph_rate)) * marza_kovanie
        total += unit_pantry
    # Sortier
    if p.sortier:
        unit_s = (PRICES["sortier_price"] * (1 + dph_rate)) * marza_kovanie
        total += unit_s
    # Skrytý kávovar
    if p.hidden_coffee:
        unit_c = (PRICES["hidden_coffee_price"] * (1 + dph_rate)) * marza_kovanie
        total += unit_c
    return total

# 7) Logistika – doprava a vynáška
def calculate_logistika(p: LeadIn) -> Tuple[float, float]:
    c_dopr = PRICES["doprava_per_km"] * p.distance_km
    total_length = p.length_spod + p.length_spod_vrch + p.length_full
    c_vynaska = PRICES["vynaska_per_floor_per_m"] * p.floors * total_length
    return c_dopr, c_vynaska

# 8) Celkový výpočet vrátane montáže a zľavy
def calculate_total(p: LeadIn) -> Tuple[float, dict]:
    c_korpus = calculate_korpus(p)
    c_dv = calculate_dvierka(p)
    c_pr = calculate_prac_doska(p)
    c_zas = calculate_zastena(p) if p.zastena else 0.0
    c_isl = calculate_island(p)
    c_ex = calculate_extras(p)
    subtotal = c_korpus + c_dv + c_pr + c_zas + c_isl + c_ex + (p.extra_price or 0)
    c_mont = subtotal * PRICES["montaz_pct"]
    c_dopr, c_vyn = calculate_logistika(p)
    subtotal_after_discount = subtotal * (1 - p.discount_pct) - p.discount_abs
    total_without_dph = math.ceil((subtotal_after_discount + c_mont + c_dopr + c_vyn) / 20) * 20
    total_with_dph = math.ceil(total_without_dph * (1 + PRICES["dph"]) / 20) * 20
    breakdown = {
        "korpus": c_korpus,
        "dvierka": c_dv,
        "prac_doska": c_pr,
        "zastena": c_zas,
        "ostrov": c_isl,
        "kovania": c_ex,
        "extra": p.extra_price or 0,
        "subtotal": subtotal,
        "montaz": c_mont,
        "doprava": c_dopr,
        "vynaska": c_vyn,
        "Cena bez DPH": total_without_dph,
        "Cena s DPH": total_with_dph
    }
    return total_with_dph, breakdown
