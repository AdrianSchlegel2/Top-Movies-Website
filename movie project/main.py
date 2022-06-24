from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange
import requests
from sqlalchemy import Integer, String, Column, Float
import os


TMDB_API_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_API_URL_FINDMOVIE = "https://api.themoviedb.org/3/movie"
TMDB_API_KEY = os.environ["tmdb_api_key"]
TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ["secret_key"]
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top-movie-list.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
Bootstrap(app)
db = SQLAlchemy(app)


class Movies(db.Model):
    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True, nullable=False)
    year = Column(Integer, unique=False, nullable=False)
    description = Column(String, unique=True, nullable=False)
    rating = Column(Float, unique=False, nullable=True)
    ranking = Column(Integer, unique=True, nullable=True)
    review = Column(String, unique=False, nullable=True)
    img_url = Column(String, unique=True, nullable=True)


class MovieForm(FlaskForm):
    rating = FloatField("Your Rating Out of 10 e.g. 7.5", validators=[DataRequired(), NumberRange(min=0, max=10)])
    review = StringField("Your Review", validators=[DataRequired()])
    enter = SubmitField("Done")


class MovieAddForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    enter = SubmitField("Add Movie")


@app.route("/")
def home():
    movies_ordered = Movies.query.order_by(Movies.rating).all()
    n = len(movies_ordered)
    for i in movies_ordered:
        i.ranking = n
        n -= 1
    return render_template("index.html", movies=movies_ordered)


@app.route("/edit/id=<movie_id>", methods=["POST", "GET"])
def edit(movie_id):
    form = MovieForm()
    if form.validate_on_submit():
        rating = form.rating.data
        review = form.review.data
        movie_change = Movies.query.get(movie_id)
        movie_change.rating = rating
        movie_change.review = f'"{review}"'
        db.session.commit()
        return redirect(url_for("home"))
    else:
        return render_template("edit.html", form=form)


@app.route("/delete/id=<movie_id>")
def delete(movie_id):
    movie_delete = Movies.query.get(movie_id)
    db.session.delete(movie_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["POST", "GET"])
def add():
    form = MovieAddForm()

    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(url=TMDB_API_URL, params={"query": movie_title, "api_key": TMDB_API_KEY})
        response.raise_for_status()
        data = response.json()
        movie_data = data["results"]
        return render_template("select.html", data=movie_data)
    return render_template("add.html", form=form)


@app.route("/find_movie/id=<movie_id>")
def find_movie(movie_id):
    response = requests.get(f"{TMDB_API_URL_FINDMOVIE}/{movie_id}", params={"api_key": TMDB_API_KEY})
    data = response.json()
    try:
        temp_dict = {
            "title": data["original_title"],
            "img_url": f'{TMDB_IMAGE_URL}{data["belongs_to_collection"]["poster_path"]}',
            "year": data["release_date"].split("-")[0],
            "description": data["overview"],
        }

        new_movie = Movies(
            title=temp_dict["title"],
            year=temp_dict["year"],
            img_url=temp_dict["img_url"],
            description=temp_dict["description"],
        )

    except TypeError:
        temp_dict = {
            "title": data["original_title"],
            "year": data["release_date"].split("-")[0],
            "description": data["overview"],
        }

        new_movie = Movies(
            title=temp_dict["title"],
            year=temp_dict["year"],
            description=temp_dict["description"],
        )

    db.session.add(new_movie)
    db.session.commit()
    movie_in_db = Movies.query.filter_by(title=temp_dict["title"]).first()
    change_movie_id = movie_in_db.id
    return redirect(url_for("edit", movie_id=change_movie_id))


if __name__ == '__main__':
    app.run(debug=True)
