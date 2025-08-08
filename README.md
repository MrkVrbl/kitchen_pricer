# Kitchen Pricer Project – Kompletná Revizia po SQLModel Chybe

V tejto verzii sme odstránili problém s ukladaním Pydantic objektu do SQLite a prepracovali `models.py` tak, aby všetky stĺpce mali platné SQLAlchemy typy.

---
### > README.md
```markdown
# Kitchen Pricer Project (Finalná Revizia)

Aplikácia na výpočet orientačnej ceny kuchyne podľa internej firemnej logiky.

## Funkcie
- **Modulárna architektúra**: všetky ceny a koeficienty v `config/prices.yaml`.
- **Streamlit UI**: 5-krokový wizard so živým prehľadom ceny a možnosťou editácie po uložení.
- **SQLite persistence**: každý lead sa ukladá so štruktúrovanými údajmi.
- **Google API**: vzdialenosť automaticky vypočítaná z adresy.

## Inštalácia & Spustenie
1. Klonujte alebo skopírujte tento adresár.
2. Vo vašom termináli:
   ```bash
   cd kitchen_pricer
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Spustite aplikáciu:
   ```bash
   streamlit run app.py
   ```
4. Otvorte prehliadač na `http://localhost:8501`.

## Štruktúra projektu
```
kitchen_pricer/
├─ README.md
├─ requirements.txt
├─ settings.toml      # Google API key
├─ logo.png
├─ config/
│   └─ prices.yaml    # firemná `prices_new.yaml`
├─ pricing/
│   ├─ __init__.py
│   ├─ config.py      # načítanie YAML a nastavení
│   ├─ models.py      # SQLModel a Pydantic schémy
│   ├─ calculator.py  # kalkulačná logika
│   └─ db.py          # SQLite CRUD
├─ app.py             # Streamlit aplikácia
└─ tests/
    └─ test_calculator.py  # Pytest testy
```

