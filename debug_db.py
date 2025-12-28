from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class TestTable(Base):
    __tablename__ = 'test_table'
    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(String)

engine = create_engine('sqlite:///test.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

t = TestTable(data="test")
session.add(t)
session.commit()
print(f"Inserted ID: {t.id}")
