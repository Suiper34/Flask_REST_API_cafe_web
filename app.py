from random import choice

from flask import Flask, flash, jsonify, request
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, select
from sqlalchemy.exc import IntegrityError, NoSuchTableError
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
    """
    GET:
        retrieves a random cafe from the database.

    Returns:
        JSON: a single random cafe's details
        Error: if cafe table doesn't exist (flashes error message)
    """

    try:
        result = db.session.execute(select(Cafe))
        all_cafes = result.scalars().all()
        rand_cafe = choice(all_cafes)
        return jsonify(cafe=rand_cafe.to_dict())
    except NoSuchTableError as e:
        flash(f'Table doesn\'t exist: {e}', category='error')


@app.route('/all-cafes')
def all_cafes():
    """
    GET:
        retrieves all cafes from the database.

    Returns:
        JSON: list of all cafes' details
        Error: if cafe table doesn't exist (flashes error message)
    """
    try:
        result = db.session.execute(select(Cafe))
        all_cafes = result.scalars().all()
        return jsonify(cafes=[cafe.to_dict() for cafe in all_cafes])

    except NoSuchTableError as e:
        flash(f'Table doesn\'t exist: {e}!', category='error')


@app.route('/search/<string:cafe_location>')
def cafes_in_location(location: str):
    """
    GET:
        retrieves all cafes in a specified location.

    Args:
        location (str): the location to search for cafes

    Returns:
        JSON: list of cafes in the specified location
        Error 404: if no cafes found in location (with error message)
    """
    the_location = db.session.get(Cafe, location)
    if not the_location:
        flash('Location has no cafe recorded!', category='error')
        return jsonify(error={
            'Not Found': f'Sorry, we ain\'t get no cafe at {the_location}'
        }), 404
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
    """
    POST:
        adds a new cafe to the database.

    Returns:
        JSON: success/error message
        200: if cafe added successfully
        Error: if cafe exists or data is invalid
    """
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
        }), 200

    except (IntegrityError, ValueError) as e:
        return jsonify(response={
            'error': f'failed to add cafe: {e}!'
        })


@app.route('/change-coffee-price/<int:cafe_id>', methods=['PATCH'])
def change_coffee_price(cafe_id: int):
    """
    PATCH
        updates coffee price for a specific cafe.

    Args:
        cafe_id (int): ID of cafe to update

    Query Parameters:
        new_price (str): new coffee price

    Returns:
        JSON: success/error message
        200: if price updated successfully
        404: if cafe not found
    """
    new_price: str = request.args.get('new_price')
    cafe_to_update_coffee_price: Cafe = db.session.get(Cafe, cafe_id)
    if not cafe_to_update_coffee_price:
        flash('Cafe not recorded!', category='error')
        return jsonify(error={
            'Not found': 'Cafe to make update on is not recorded yet!'
        }), 404

    cafe_to_update_coffee_price.coffee_price = new_price,
    db.session.commit()
    flash('Price updated successfully!', category='success')
    return jsonify(response={
        'success': 'Coffee price has been updated!'
    })


@app.route('/delete-cafe/<int:cafe_id>', methods=['DELETE', 'POST', 'GET'])
def delete_cafe(cafe_id):
    """
    DELETE/POST/GET /delete-cafe/<cafe_id>
        deletes a cafe from the database (requires API key).

    Args:
        cafe_id (int): ID of cafe to delete

    Query Parameters:
        api-key (str): authorization key (must be "Authorization_Key")

    Returns:
        JSON: success/error message
        200: if deleted successfully
        403: if API key is missing or invalid
        404: if cafe not found
    """
    API_KEY = request.args.get('api-key')
    cafe_to_delete = db.session.get(Cafe, cafe_id)

    if not API_KEY or API_KEY != 'Authorization_Key':
        return jsonify(error={
            'Forbidden': 'Not allowed, wrong API key!'
        }), 403
    else:
        if not cafe_to_delete:
            return jsonify(error={
                'Not found': 'Cafe not found!'
            }), 404

        try:
            db.session.delete(cafe_to_delete)
            db.session.commit()
            flash('Cafe deleted', category='success')
        except Exception as e:
            flash(f'Failed to delete cafe!: {e}', category='danger')


if __name__ == '__main__':
    app.run(debug=True)
