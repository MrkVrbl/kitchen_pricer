from sqlmodel import SQLModel, Session, create_engine, select
from pricing.models import Lead

DATABASE_URL = "sqlite:///kitchen_pricer.db"
engine = create_engine(DATABASE_URL, echo=False)

def get_session():
    return Session(engine)

def init_db():
    from pricing.models import Lead  # importuj všetky modely
    with get_session() as session:
        SQLModel.metadata.create_all(session.get_bind())

def save_lead(lead_in):
    from pricing.models import Lead
    with Session(engine) as session:
        if getattr(lead_in, "id", None):  # UPDATE
            db_record = session.get(Lead, lead_in.id)
            if db_record:
                db_record.data = lead_in.dict()
                db_record.quoted_price = lead_in.quoted_price
                session.commit()
                return db_record.id
        # CREATE
        db_record = Lead(data=lead_in.dict(), quoted_price=lead_in.quoted_price)
        session.add(db_record)
        session.commit()
        session.refresh(db_record)
        return db_record.id

def get_all_leads():
    with Session(engine) as session:
        results = session.exec(select(Lead)).all()
        return results

def delete_lead(lead_id: int):
    from pricing.models import Lead
    from pricing.db import get_session
    with get_session() as session:
        lead = session.get(Lead, lead_id)
        if lead:
            session.delete(lead)
            session.commit()

# Spusti raz v termináli alebo na začiatku aplikácie:
if __name__ == "__main__":
    init_db()