from sqlalchemy import create_engine

database_address = "sqlite:///erp.db"
database_engine = create_engine(database_address)