from random import choice

from flask import Flask, flash, jsonify, request
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, select, update
from sqlalchemy.exc import IntegrityError, NoSuchColumnError, NoSuchTableError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


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
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db.init_app(app)
api = Api(app, catch_all_404s=True)


@app.route('/random')
def random_cafe():
    try:
        result = db.session.execute(select(Cafe))
        all_cafes = result.scalars().all()
        rand_cafe = choice(all_cafes)
        return jsonify(cafe=rand_cafe.to_dict())
    except NoSuchTableError as e:
        flash(f'Table doesn\'t exist: {e}', category='error')


@app.route('/all-cafes')
def all_cafes():
    try:
        result = db.session.execute(select(Cafe))
        all_cafes = result.scalars().all()
        return jsonify(cafes=[cafe.to_dict() for cafe in all_cafes])

    except NoSuchTableError as e:
        flash(f'Table doesn\'t exist: {e}!', category='error')


@app.route('/search/<string:cafe_location>')
def cafes_in_location(location: str):
    the_location = db.session.get(Cafe, location)
    if not the_location:
        flash('Location has no cafe recorded!', category='error')
        return jsonify(error={
            'Not Found': f'Sorry, we ain\'t get no cafe at {the_location}'
        })
    try:
        result = db.session.execute(
            select(Cafe).where(Cafe.location == the_location)
        )
        the_location_cafes = result.scalars().all()
        return jsonify(
            cafe_at_location=[cafe.to_dict() for cafe in the_location_cafes])

    except (Exception) as e:
        flash(f'{e}')


@app.route('/add-cafe', methods=['POST'])
def add_cafe():
    try:
        new_cafe = Cafe(
            name=request.form.get('name'),
            map_url=request.form.get('map_url'),
            img_url=request.form.get('img_url'),
            location=request.form.get('location'),
            seats=request.form.get('seats'),
            has_toilet=request.form.get('has_toilet', type=bool),
            has_wifi=request.form.get('has_wifi', type=bool),
            has_sockets=request.form.get('has_sockets', type=bool),
            can_take_calls=request.form.get('can_take_calls', type=bool),
            coffee_price=request.form.get('coffee_price'),
        )
        db.session.add(new_cafe)
        db.session.commit()
        flash('Successfully added', category='success`')
        return jsonify(response={
            'success': 'Cafe successfully added!'
        })

    except (IntegrityError, ValueError) as e:
        return jsonify(response={
            'error': f'failed to add cafe: {e}!'
        })


@app.route('/change-coffee-price/<int:cafe_id>', methods=['PATCH'])
def change_coffee_price(cafe_id: int):
    new_price: str = request.args.get('new_price')
    cafe_to_update_coffee_price: Cafe = db.session.get(Cafe, cafe_id)
    if not cafe_to_update_coffee_price:
        flash('Cafe not recorded!', category='error')
        return jsonify(response={
            'error': 'Cafe to make update on is not recorded yet!'
        })

    cafe_to_update_coffee_price.coffee_price = new_price,
    db.session.commit()
    flash('Price updated successfully!', category='success')
    return jsonify(response={
        'success': 'Coffee price has been updated!'
    })


@app.route('/delete-cafe/<int:cafe_id>', methods=['DELETE'])
def delete_cafe(cafe_id):
    db.session.get(Cafe, cafe_id)
    db.session.delete()


if __name__ == '__main__':
    app.run(debug=True)
