# from sqlalchemy import Column, Integer, String, Float, Boolean
# from sqlalchemy.ext.declarative import declarative_base

# Base = declarative_base()

# class DivarProperty(Base):
#     __tablename__ = "divar_data"

#     id = Column(Integer, primary_key=True, index=True)
#     status = Column(String)
#     title = Column(String)
#     description = Column(String)
#     property_type = Column(String)
#     transaction_type = Column(String)
#     price = Column(Float)
#     area = Column(Integer)
#     vpm = Column(Float)
#     city = Column(String)
#     district = Column(String)
#     bedrooms = Column(Integer)
#     year_built = Column(Integer)
#     floor = Column(Integer)
#     total_floors = Column(Integer)
#     units = Column(Integer)
#     document_type = Column(String)
#     has_parking = Column(Boolean, default=False)
#     has_elevator = Column(Boolean, default=False)
#     has_storage = Column(Boolean, default=False)
#     is_renovated = Column(Boolean, default=False)
#     open_to_exchange = Column(Boolean, default=False)
#     exchange_preference = Column(String)
#     source_link = Column(String)
#     image_url = Column(String)
