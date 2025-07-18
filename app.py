from random import choice

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_restful import Resource, Api


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class Cafe(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True)
    map_url: Mapped[str] = mapped_column(String(500))
    img_url: Mapped[str] = mapped_column(String(500))
    location: Mapped[str] = mapped_column(String(250))
    seats: Mapped[str] = mapped_column(String(250))
    has_toilet: Mapped[bool]
    has_wifi: Mapped[bool]
    has_sockets: Mapped[bool]
    can_take_calls: Mapped[bool]
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

    def to_dict(self) -> dict:
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db.init_app(app)
api = Api(app, catch_all_404s=True)


@app.route('/random')
def random_cafe():
    result = db.session.execute(select(Cafe))
    all_cafes = result.scalars().all()
    rand_cafe = choice(all_cafes)
    return jsonify(cafe=rand_cafe.to_dict())


@app.route('/all-cafes')
def all_cafes():
    result = db.session.execute(select(Cafe))
    all_cafes = result.scalars().all()
    return jsonify(cafes=[cafe.to_dict() for cafe in all_cafes])


if __name__ == '__main__':
    app.run(debug=True)
