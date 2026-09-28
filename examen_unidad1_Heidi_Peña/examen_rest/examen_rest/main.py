import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
from models import Laptop


class LaptopCreate(BaseModel):
    marca: str
    modelo: str
    ram_gb: int


def laptop_a_dict(laptop: Laptop) -> dict:
    return {
        "id": laptop.id,
        "marca": laptop.marca,
        "modelo": laptop.modelo,
        "ram_gb": laptop.ram_gb,
        "disponible": laptop.disponible,
    }


def esperar_mysql(intentos: int = 30, espera: float = 2.0) -> None:
    """MySQL puede tardar unos segundos en aceptar conexiones."""
    for _ in range(intentos):
        try:
            with engine.connect():
                return
        except OperationalError:
            time.sleep(espera)
    raise RuntimeError("MySQL no aceptó conexiones a tiempo")


def carga_inicial() -> None:
    db = SessionLocal()
    try:
        if db.query(Laptop).count() == 0:
            db.add_all(
                [
                    Laptop(id=1, marca="Dell", modelo="Latitude 5440", ram_gb=16, disponible=True),
                    Laptop(id=2, marca="Lenovo", modelo="ThinkPad E14", ram_gb=8, disponible=False),
                    Laptop(id=3, marca="HP", modelo="ProBook 450", ram_gb=16, disponible=True),
                ]
            )
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    esperar_mysql()
    Base.metadata.create_all(bind=engine)
    carga_inicial()
    yield


app = FastAPI(lifespan=lifespan)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def raiz():
    return {"mensaje": "API del laboratorio de cómputo"}


@app.get("/laptops")
def listar_laptops(db: Session = Depends(get_db)):
    laptops = db.query(Laptop).order_by(Laptop.id).all()
    return [laptop_a_dict(l) for l in laptops]


# Debe ir antes de /laptops/{laptop_id}
@app.get("/laptops/disponibles")
def listar_disponibles(db: Session = Depends(get_db)):
    laptops = (
        db.query(Laptop).filter(Laptop.disponible.is_(True)).order_by(Laptop.id).all()
    )
    return [laptop_a_dict(l) for l in laptops]


@app.get("/laptops/{laptop_id}")
def obtener_laptop(laptop_id: int, db: Session = Depends(get_db)):
    laptop = db.query(Laptop).filter(Laptop.id == laptop_id).first()
    if laptop is None:
        raise HTTPException(status_code=404, detail="Laptop no encontrada")
    return laptop_a_dict(laptop)


@app.post("/laptops")
def crear_laptop(datos: LaptopCreate, db: Session = Depends(get_db)):
    nueva = Laptop(
        marca=datos.marca,
        modelo=datos.modelo,
        ram_gb=datos.ram_gb,
        disponible=True,
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return laptop_a_dict(nueva)
