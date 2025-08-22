import streamlit as st
from datetime import date
from pathlib import Path
from pricing.models import LeadIn
from pricing.calculator import calculate_total
from pricing.db import save_lead, get_all_leads, delete_lead
from pricing.config import PRICES, SETTINGS

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Kitchen Pricer Interná Aplikácia", layout="wide")
st.title("Kitchen Pricer – Vnútorná Kalkulačka")

# --- SESSION STATE INITIALIZATION ---
fields_defaults = {
    "customer_name": "",
    "address": "",
    "floors": 0,
    "distance_km": 0.0,
    "length_spod": 0.0,
    "length_spod_vrch": 0.0,
    "length_full": 0.0,
    "shape": "rovný",
    "has_island": False,
    "length_island": 0.0,
    "material_dvierok": "",
    "material_pracovnej_dosky": "",
    "led_pas": False,
    "drawer_count": 0,
    "vrchne_otvaranie_typ": "",
    "vrchne_doors_count": 0,
    "rohovy_typ": False,
    "potravinova_skrina_typ": "",
    "potravinove_sufle_typ": "",
    "sortier": False,
    "hidden_coffee": False,
    "zastena": False,
    "discount_pct": 0.0,
    "discount_abs": 0.0,
    "extra_desc": "",
    "extra_price": 0.0,
    # New field: date when kitchen should be ready
    "realization_date": date.today(),
    "attachments": [],
}

for key, default in fields_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

if "lead_id" not in st.session_state:
    st.session_state["lead_id"] = None

if "new_lead" not in st.session_state:
    st.session_state["new_lead"] = True

if "lead_select" not in st.session_state:
    st.session_state["lead_select"] = ""

if "reset_lead_select" not in st.session_state:
    st.session_state["reset_lead_select"] = False

# If flagged to reset, clear lead_select before the selectbox is rendered
if st.session_state["reset_lead_select"]:
    st.session_state["lead_select"] = ""
    st.session_state["reset_lead_select"] = False

# --- SIDEBAR UI ---
with st.sidebar:
    st.image("logo.png", use_container_width=True)
    st.write("---")

    # Button: open blank wizard for a new lead
    if st.button("➕ Nový lead"):
        for key, default in fields_defaults.items():
            st.session_state[key] = default
        st.session_state["lead_id"] = None
        st.session_state["new_lead"] = True
        st.session_state["reset_lead_select"] = True
        st.rerun()

    st.write("---")
    st.subheader("Uložené leady")
    leads = get_all_leads()
    if leads:
        lead_options = [
            f"ID {l.id} – {l.data.get('customer_name', '')} ({l.quoted_price:,.2f} €)"
            for l in leads
        ]
        selected = st.selectbox(
            "Vyber lead na zobrazenie",
            [""] + lead_options,
            key="lead_select",
        )
        if selected and selected in lead_options:
            idx = lead_options.index(selected)
            selected_lead = leads[idx]
            if st.session_state["lead_id"] != selected_lead.id:
                data = selected_lead.data
                for field_name in fields_defaults:
                    if field_name in data:
                        if field_name == "realization_date" and data[field_name]:
                            # Convert ISO string back to date
                            st.session_state[field_name] = date.fromisoformat(data[field_name])
                        else:
                            if data[field_name] is None and isinstance(fields_defaults[field_name], str):
                                st.session_state[field_name] = ""
                            else:
                                if field_name == "discount_pct" and data[field_name] is not None:
                                    st.session_state[field_name] = data[field_name] * 100
                                else:
                                    st.session_state[field_name] = data[field_name]
                    else:
                        st.session_state[field_name] = fields_defaults[field_name]
                st.session_state["lead_id"] = selected_lead.id
                st.session_state["new_lead"] = False
                st.rerun()
    else:
        st.info("Žiadne leady zatiaľ nie sú uložené.")

    st.write("---")
    # Calculate price based on current session_state
    temp_data = {}
    for field_name, default in fields_defaults.items():
        if field_name in {"realization_date", "attachments"}:
            continue  # Not part of LeadIn
        val = st.session_state[field_name]
        if field_name in {
            "material_dvierok",
            "material_pracovnej_dosky",
            "vrchne_otvaranie_typ",
            "potravinova_skrina_typ",
            "potravinove_sufle_typ",
        }:
            temp_data[field_name] = val if val != "" else None
        else:
            if field_name == "discount_pct":
                temp_data[field_name] = val / 100
            else:
                temp_data[field_name] = val

    try:
        temp_lead = LeadIn(**temp_data)
        total, breakdown = calculate_total(temp_lead)
    except Exception:
        total, breakdown = 0.0, {}

    st.subheader("Zhrnutie ceny")
    st.metric(label="Orient. cena (€)", value=f"{total:,.2f}")
    for k, v in breakdown.items():
        if k != "total":
            st.write(f"• {k.replace('_', ' ').capitalize()}: {v:,.2f} €")

# --- MAIN AREA: WIZARD (Všetko pod sebou) ---
if st.session_state["lead_id"] and not st.session_state["new_lead"]:
    st.subheader(f"Editácia leadu ID {st.session_state['lead_id']}")
else:
    st.subheader("Nový lead")

# 1. Základné údaje
st.markdown("### 📋 Základné údaje")
st.session_state["customer_name"] = st.text_input(
    "Meno zákazníka",
    value=st.session_state["customer_name"],
    key="customer_name_input",
)
st.session_state["address"] = st.text_input(
    "Adresa (ulica + PSČ)",
    value=st.session_state["address"],
    key="address_input",
)

st.session_state["realization_date"] = st.date_input(
    "Kedy by mala byť kuchyňa hotová?",
    value=st.session_state["realization_date"],
    key="realization_date_input",
)

st.session_state["floors"] = st.number_input(
    "Počet poschodí pre vynášku",
    min_value=0,
    step=1,
    value=st.session_state["floors"],
    key="floors_input",
)
st.session_state["distance_km"] = st.number_input(
    "Vzdialenosť (km)",
    min_value=0.0,
    step=1.0,
    value=st.session_state["distance_km"],
    key="distance_km_input",
)

# Attachments section
uploaded_files = st.file_uploader(
    "Prílohy (obrázky, PDF)",
    accept_multiple_files=True,
)

# Display previously saved attachments and newly uploaded files
if st.session_state["attachments"] or uploaded_files:
    st.write("Uložené súbory:")

    # Show files already saved for this lead
    if st.session_state["attachments"] and st.session_state.get("lead_id") is not None:
        base_path = Path("attachments") / str(st.session_state["lead_id"])
        for fname in st.session_state["attachments"]:
            file_path = base_path / fname
            if file_path.exists():
                if file_path.suffix.lower() in {
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".gif",
                    ".bmp",
                    ".webp",
                }:
                    st.image(file_path.read_bytes(), caption=fname)
                else:
                    with open(file_path, "rb") as f:
                        st.download_button(
                            f"📄 {fname}", f.read(), file_name=fname, key=f"download_saved_{fname}"
                        )

    # Show newly uploaded files immediately
    for uf in uploaded_files or []:
        if uf.type.startswith("image/"):
            st.image(uf, caption=uf.name)
        else:
            st.download_button(
                f"📄 {uf.name}", uf.getbuffer(), file_name=uf.name, key=f"download_new_{uf.name}"
            )

st.markdown("---")

# 2. Rozmery a tvar
st.markdown("### 📏 Rozmery a tvar")
st.session_state["length_spod"] = st.number_input(
    "Dĺžka spodných skriniek (m)",
    min_value=0.0,
    step=0.1,
    value=st.session_state["length_spod"],
    key="length_spod_input",
)
st.session_state["length_spod_vrch"] = st.number_input(
    "Dĺžka spodných + vrchných skriniek (m)",
    min_value=0.0,
    step=0.1,
    value=st.session_state["length_spod_vrch"],
    key="length_spod_vrch_input",
)
st.session_state["length_full"] = st.number_input(
    "Dĺžka vysokých skriniek (m)",
    min_value=0.0,
    step=0.1,
    value=st.session_state["length_full"],
    key="length_full_input",
)
shape_options = ["rovný", "L", "U"]
shape_index = shape_options.index(st.session_state["shape"]) if st.session_state["shape"] in shape_options else 0
st.session_state["shape"] = st.selectbox(
    "Tvar kuchyne",
    shape_options,
    index=shape_index,
    key="shape_input",
)
st.session_state["has_island"] = st.checkbox(
    "Ostrovček",
    value=st.session_state["has_island"],
    key="has_island_input",
)
st.session_state["length_island"] = st.number_input(
    "Dĺžka ostrovčeka (m)",
    min_value=0.0,
    step=0.1,
    value=st.session_state["length_island"],
    key="length_island_input",
)

st.markdown("---")

# 3. Materiály
st.markdown("### 🛠️ Materiály")
mat_dvierok_opts = ["", "laminát", "folia", "akryl", "striekane"]
initial_md = st.session_state["material_dvierok"] or ""
md_index = mat_dvierok_opts.index(initial_md) if initial_md in mat_dvierok_opts else 0
chosen_md = st.selectbox(
    "Materiál dvierok",
    mat_dvierok_opts,
    index=md_index,
    key="material_dvierok_widget",
)
st.session_state["material_dvierok"] = chosen_md

mat_prac_opts = ["", "bez", "drevodekor", "imitacia_kamena", "kompakt", "umely_kamen"]
initial_mp = st.session_state["material_pracovnej_dosky"] or ""
mp_index = mat_prac_opts.index(initial_mp) if initial_mp in mat_prac_opts else 0
chosen_mp = st.selectbox(
    "Materiál pracovnej dosky",
    mat_prac_opts,
    index=mp_index,
    key="material_pracovnej_dosky_widget",
)
st.session_state["material_pracovnej_dosky"] = chosen_mp

st.markdown("---")

# 4. Doplnky
st.markdown("### 🔧 Doplnky")
st.session_state["led_pas"] = st.checkbox(
    "LED pás",
    value=st.session_state["led_pas"],
    key="led_pas_input",
)
st.session_state["drawer_count"] = st.number_input(
    "Počet šuflíkov",
    min_value=0,
    step=1,
    value=st.session_state["drawer_count"],
    key="drawer_count_input",
)
horne_opts = ["", "zlomove", "klasik"]
initial_ho = st.session_state["vrchne_otvaranie_typ"] or ""
ho_index = horne_opts.index(initial_ho) if initial_ho in horne_opts else 0
chosen_ho = st.selectbox(
    "Horné otváranie",
    horne_opts,
    index=ho_index,
    key="vrchne_otvaranie_typ_widget",
)
st.session_state["vrchne_otvaranie_typ"] = chosen_ho

st.session_state["vrchne_doors_count"] = st.number_input(
    "Počet horných dvierok",
    min_value=0,
    step=1,
    value=st.session_state["vrchne_doors_count"],
    key="vrchne_doors_count_input",
)
st.session_state["rohovy_typ"] = st.checkbox(
    "Rohový mechanizmus",
    value=st.session_state["rohovy_typ"],
    key="rohovy_typ_input",
)
potr_skrina_opts = ["", "vysoka", "nizka"]
initial_ps = st.session_state["potravinova_skrina_typ"] or ""
ps_index = potr_skrina_opts.index(initial_ps) if initial_ps in potr_skrina_opts else 0
chosen_ps = st.selectbox(
    "Potravinová skrina",
    potr_skrina_opts,
    index=ps_index,
    key="potravinova_skrina_typ_widget",
)
st.session_state["potravinova_skrina_typ"] = chosen_ps

potr_sufle_opts = ["", "vysoke", "nizke"]
initial_pu = st.session_state["potravinove_sufle_typ"] or ""
pu_index = potr_sufle_opts.index(initial_pu) if initial_pu in potr_sufle_opts else 0
chosen_pu = st.selectbox(
    "Potravinové šufle",
    potr_sufle_opts,
    index=pu_index,
    key="potravinove_sufle_typ_widget",
)
st.session_state["potravinove_sufle_typ"] = chosen_pu

st.session_state["sortier"] = st.checkbox(
    "Sortier",
    value=st.session_state["sortier"],
    key="sortier_input",
)
st.session_state["hidden_coffee"] = st.checkbox(
    "Skrytý kávovar",
    value=st.session_state["hidden_coffee"],
    key="hidden_coffee_input",
)
st.session_state["zastena"] = st.checkbox(
    "Zástena",
    value=st.session_state["zastena"],
    key="zastena_input",
)
st.session_state["extra_desc"] = st.text_input(
    "Extra požiadavka (popis)",
    value=st.session_state["extra_desc"],
    key="extra_desc_input",
)
st.session_state["extra_price"] = st.number_input(
    "Cena extra požiadavky (€)",
    min_value=0.0,
    step=10.0,
    value=st.session_state["extra_price"],
    key="extra_price_input",
)

st.markdown("---")

# 5. Zľavy
st.markdown("### 💰 Zľavy")
# Oprav hodnotu pred widgetom
if st.session_state["discount_pct"] > 100.0:
    st.session_state["discount_pct"] = 100.0
if st.session_state["discount_pct"] < 0.0:
    st.session_state["discount_pct"] = 0.0

st.session_state["discount_pct"] = st.number_input(
    "Zľava (%)",
    min_value=0.0,
    max_value=100.0,
    step=1.0,
    value=st.session_state["discount_pct"],
    key="discount_pct_input",
)
st.session_state["discount_abs"] = st.number_input(
    "Zľava (€)",
    min_value=0.0,
    step=1.0,
    value=st.session_state["discount_abs"],
    key="discount_abs_input",
)

st.markdown("---")


# --- ACTION BUTTONS (Uložiť / Vymazať) ---
col1, col2 = st.columns(2)
with col1:
    if st.button("💾 Uložiť lead"):
        if not st.session_state["customer_name"] or not st.session_state["address"]:
            st.error("Vyplňte meno zákazníka a adresu.")
        else:
            # Build dict for LeadIn (exclude realization_date)
            lead_kwargs = {}
            for field_name, default in fields_defaults.items():
                if field_name in {"realization_date", "attachments"}:
                    continue
                val = st.session_state[field_name]
                if field_name in {
                    "material_dvierok",
                    "material_pracovnej_dosky",
                    "vrchne_otvaranie_typ",
                    "potravinova_skrina_typ",
                    "potravinove_sufle_typ",
                }:
                    lead_kwargs[field_name] = val if val != "" else None
                else:
                    if field_name == "discount_pct":
                        lead_kwargs[field_name] = val / 100
                    else:
                        lead_kwargs[field_name] = val

            new_files = [f.name for f in uploaded_files] if uploaded_files else []
            lead_kwargs["attachments"] = st.session_state["attachments"] + new_files

            if st.session_state["lead_id"]:
                lead_kwargs["id"] = st.session_state["lead_id"]

            lead_in = LeadIn(**lead_kwargs)
            total, breakdown = calculate_total(lead_in)
            lead_data = lead_in.dict()
            lead_data["quoted_price"] = breakdown.get("Cena s DPH", 0.0)
            # Add realization_date as ISO string
            lead_data["realization_date"] = st.session_state["realization_date"].isoformat()

            class LeadObj:
                def __init__(self, data):
                    self.__dict__.update(data)

                def dict(self):
                    return self.__dict__

            saved_id = save_lead(LeadObj(lead_data))

            if uploaded_files:
                dest = Path("attachments") / str(saved_id)
                dest.mkdir(parents=True, exist_ok=True)
                for f in uploaded_files:
                    with open(dest / f.name, "wb") as out:
                        out.write(f.getbuffer())
                st.session_state["attachments"].extend(new_files)

            st.success(f"Lead uložený s ID {saved_id}")

            st.session_state["lead_id"] = saved_id
            st.session_state["new_lead"] = False
            st.session_state["reset_lead_select"] = True
            st.rerun()

with col2:
    if not st.session_state["new_lead"]:
        if st.button("🗑️ Vymazať lead"):
            delete_lead(st.session_state["lead_id"])
            st.success("Lead bol vymazaný.")
            for key, default in fields_defaults.items():
                st.session_state[key] = default
            st.session_state["lead_id"] = None
            st.session_state["new_lead"] = True
            st.session_state["reset_lead_select"] = True
            st.rerun()

# --- RÝCHLY SUMÁR PRE KOPÍROVANIE ---
lead_summary = []
lead_summary.append(f"Meno zákazníka: {st.session_state['customer_name']}")
lead_summary.append(f"Adresa: {st.session_state['address']}")
lead_summary.append(f"Termín realizácie: {st.session_state['realization_date'].strftime('%d.%m.%Y')}")
lead_summary.append(f"Počet poschodí pre vynášku: {st.session_state['floors']}")
lead_summary.append(f"Vzdialenosť: {st.session_state['distance_km']} km")
lead_summary.append(f"Tvar kuchyne: {st.session_state['shape']}")
lead_summary.append(f"Dĺžka spodných skriniek: {st.session_state['length_spod']} m")
lead_summary.append(f"Dĺžka spodných + vrchných skriniek: {st.session_state['length_spod_vrch']} m")
lead_summary.append(f"Dĺžka vysokých skriniek: {st.session_state['length_full']} m")
lead_summary.append(f"Ostrovček: {'áno' if st.session_state['has_island'] else 'nie'}")
if st.session_state['has_island']:
    lead_summary.append(f"Dĺžka ostrovčeka: {st.session_state['length_island']} m")
lead_summary.append(f"Materiál dvierok: {st.session_state['material_dvierok']}")
lead_summary.append(f"Materiál pracovnej dosky: {st.session_state['material_pracovnej_dosky']}")
lead_summary.append(f"LED pás: {'áno' if st.session_state['led_pas'] else 'nie'}")
lead_summary.append(f"Počet šuflíkov: {st.session_state['drawer_count']}")
lead_summary.append(f"Horné otváranie: {st.session_state['vrchne_otvaranie_typ']}")
lead_summary.append(f"Počet horných dvierok: {st.session_state['vrchne_doors_count']}")
lead_summary.append(f"Rohový mechanizmus: {'áno' if st.session_state['rohovy_typ'] else 'nie'}")
lead_summary.append(f"Potravinová skrina: {st.session_state['potravinova_skrina_typ']}")
lead_summary.append(f"Potravinové šufle: {st.session_state['potravinove_sufle_typ']}")
lead_summary.append(f"Sortier: {'áno' if st.session_state['sortier'] else 'nie'}")
lead_summary.append(f"Skrytý kávovar: {'áno' if st.session_state['hidden_coffee'] else 'nie'}")
lead_summary.append(f"Zástena: {'áno' if st.session_state['zastena'] else 'nie'}")
if st.session_state['extra_desc']:
    lead_summary.append(f"Extra požiadavka: {st.session_state['extra_desc']} ({st.session_state['extra_price']} €)")
if st.session_state['discount_pct']:
    lead_summary.append(f"Zľava: {st.session_state['discount_pct']} %")
if st.session_state['discount_abs']:
    lead_summary.append(f"Zľava absolútna: {st.session_state['discount_abs']} €")


st.markdown("### ✉️ Rýchly sumár pre zákazníka")
st.code("\n".join(lead_summary), language="markdown")
