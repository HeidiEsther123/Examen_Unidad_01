from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Dentro del contenedor, el host es el nombre del servicio: mysql
DATABASE_URL = "mysql+pymysql://laboratorio:laboratorio@mysql:3306/laboratorio"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
