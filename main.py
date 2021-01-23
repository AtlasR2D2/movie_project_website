from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

MOVIE_DB_API_KEY = os.environ["TMDB_API_KEY"]
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_IMAGE_URL = ""

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

Bootstrap(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, unique=False, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Float, nullable=False)
    review = db.Column(db.String(250), unique=True, nullable=True)
    img_url = db.Column(db.String(250), unique=True, nullable=False)


# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, "
#                 "pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, "
#                 "Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )


class EditMovieEntryForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")

class AddMovieEntryForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")

db.create_all()
#
# db.session.add(new_movie)
# db.session.commit()


@app.route("/")
def home():
    # movies = db.session.query(Movie).all()
    # for movie in movies:
    #     print(movie.title)
    # This line creates a list of all the movies sorted by rating
    all_movies = Movie.query.order_by(Movie.rating).all()

    # This line loops through all the movies
    for i in range(len(all_movies)):
        # This line gives each movie a new ranking reversed from their order in all_movies
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)

@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = EditMovieEntryForm()
    movie_to_update = Movie.query.get(request.args.get("id_x"))
    if form.validate_on_submit():
        movie_to_update.review = form.review.data
        movie_to_update.rating = float(form.rating.data)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", movie=movie_to_update, form=form)


@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("id_x")
    movie = Movie.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddMovieEntryForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(MOVIE_DB_SEARCH_URL, params={"api_key": MOVIE_DB_API_KEY, "query": movie_title})
        response.raise_for_status()
        results_json_data = response.json()["results"]
        return render_template("select.html", options=results_json_data)
    return render_template("add.html", form=form)


@app.route("/add-details",methods=["GET","POST"])
def add_details():
    movie_id = request.args.get("id")
    print(movie_id)
    movie_id = "{" + str(movie_id) + "}"
    url_get = f"{MOVIE_DB_SEARCH_URL}/{movie_id}?api_key={MOVIE_DB_API_KEY}"
    print(url_get)
    response = requests.get(url_get)#, params={"api_key": MOVIE_DB_API_KEY, "language": "en-US"})
    # response.raise_for_status()
    data = response.json()
    new_movie = Movie(
        title=data["title"],
        # The data in release_date includes month and day, we will want to get rid of.
        year=data["release_date"].split("-")[0],
        img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
        description=data["overview"]
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for("edit", movie_id))


if __name__ == '__main__':
    app.run(debug=True)
