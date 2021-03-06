from sqlalchemy import (create_engine,
                        Column,
                        String,
                        Integer,
                        Table,
                        ForeignKey)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Base, Product, User, db_string

# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance

db = create_engine(db_string)
Base = declarative_base()

Session = sessionmaker(db)
session = Session()

# Create dummy user
User1 = User(name="John Rusty", email="rustyjohn@products.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')  # NOQA
session.add(User1)
session.commit()

# Add suspension category
category1 = Category(user_id=1, name="Suspension")

session.add(category1)
session.commit()

# Add items in suspension category
product1 = Product(user_id=1, name="Fox Front Shocks",
                   description="Fox Shocks are used in off-road vehicles. Comfort and endurance in all-terrain.",  # NOQA
                   price="$250.99", picture="https://cdn3.volusion.com/sxegw.zwlry/v/vspfiles/photos/FOX-883-24-02X-2.jpg",  # NOQA
                   category=category1)
session.add(product1)
session.commit()

product2 = Product(user_id=1, name="Coil Springs", description="Restore OEM-standard handling and smoother ride to your vehicle.",  # NOQA
                   price="$45.00",
                   picture="https://content.speedwaymotors.com/ProductImages/252512_L1600_5a117319-e7af-4420-8c42-c7bcdf6db5fd.jpg",  # NOQA
                   category=category1)
session.add(product2)
session.commit()

# Add lightning category
category2 = Category(user_id=1, name="Lightning")

session.add(category2)
session.commit()

# Add items in suspension category
product1 = Product(user_id=1, name="H7 Led Bulb",
                   description="Each bulb has 2 pcs of high power COB chips made in Taiwan, perfect light pattern without dark spot,6000-6500K",  # NOQA
                     price="$20.98", picture="http://www.caravanparkproducts.co.uk/advtiserlogos/no-image.jpg", category=category2)  # NOQA
session.add(product1)
session.commit()

product2 = Product(user_id=1, name="Led Light Bar",
                   description="The appropriate mix and match of spot beams and flood beams provides a long irradiation distance and broad view.",  # NOQA
                     price="$27.41", picture="https://b.cdnbrm.com/images/products/large/lights/double_row_cree_led_light_bars_hero.jpg", category=category2)  # NOQA
session.add(product2)
session.commit()

# Add lights category
category3 = Category(user_id=1, name="Brake System")

session.add(category3)
session.commit()

# Add lights category
category4 = Category(user_id=1, name="Tires")

session.add(category4)
session.commit()

print("Added initial categories and products!")
