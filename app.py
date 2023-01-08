# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, Venue, Artist, Show
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm as Form
from sqlalchemy.sql.functions import func

from forms import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db.init_app(app)
migrate = Migrate(app, db)


# TODO: connect to a local postgresql database

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en")


app.jinja_env.filters["datetime"] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    # TODO: replace with real venues data.
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    areas = db.session.query(Venue).all()
    final_areas = []

    data = {}
    for area in areas:
        city = area.city
        state = area.state
        if city not in data:
            data[city] = {"state": state, "venues": []}
        data[city]["venues"].append(
            {
                "id": area.id,
                "name": area.name,
                "num_upcoming_shows": (
                    db.session.query(func.count(Show.id))
                    .filter(Show.venue_id == Venue.id)
                    .filter(Show.start_time > datetime.now())
                    .scalar()
                ),
            }
        )
    for city in data.keys():
        final_areas.append(
            dict(city=city, state=data[city]["state"], venues=data[city]["venues"])
        )

    return render_template("pages/venues.html", areas=final_areas)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # search for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get("search_term", "")
    searched_venues = (
        db.session.query(Venue)
        .filter(func.lower(Venue.name).like(f"%{search_term}%"))
        .all()
    )

    response = {"count": len(searched_venues), "data": []}
    for venue in searched_venues:
        response["data"].append(
            {
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": (
                    db.session.query(func.count(Show.id))
                    .filter(Show.venue_id == venue.id)
                    .filter(Show.start_time > datetime.now())
                    .scalar()
                ),
            }
        )

    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.filter(Venue.id == venue_id).first()
    past_shows = (
        db.session.query(Show, Artist)
        .join(Artist, Show.artist_id == Artist.id)
        .filter(Show.venue_id == venue_id)
        .filter(Show.start_time < datetime.now())
        .all()
    )
    upcoming_shows = (
        db.session.query(Show, Artist)
        .join(Artist, Show.artist_id == Artist.id)
        .filter(Show.venue_id == venue_id)
        .filter(Show.start_time > datetime.now())
        .all()
    )

    past = []
    for show, artist in past_shows:
        past.append(
            {
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": str(show.start_time),
            }
        )

    upcoming = []
    for show, artist in upcoming_shows:
        upcoming.append(
            {
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": str(show.start_time),
            }
        )

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past,
        "upcoming_shows": upcoming,
        "upcoming_shows_count": len(upcoming),
    }
    return render_template("pages/show_venue.html", venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = VenueForm(request.form, meta={"csrf": False})
    if form.validate():
        try:
            venue = Venue(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                address=form.address.data,
                phone=form.phone.data,
                image_link=form.image_link.data,
                facebook_link=form.facebook_link.data,
                seeking_talent=form.seeking_talent.data,
                seeking_description=form.seeking_description.data,
                genres=form.genres.data,
                website=form.website_link.data,
            )

            db.session.add(venue)
            db.session.commit()
            flash("Venue " + request.form["name"] + " was successfully listed!")
        except ValueError as e:
            flash(
                "An error occurred. Venue "
                + request.form["name"]
                + " could not be listed."
            )
            print(e)
            db.session.rollback()
        finally:
            db.session.close()

    else:
        message = []
        for field, err in form.errors.items():
            message.append(field + " " + "|".join(err))
        flash("Errors " + str(message))
        form = VenueForm()
        return render_template("forms/new_venue.html", form=form)
    return render_template("pages/home.html")

    # on successful db insert, flash success
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/


@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    # TODO: replace with real data returned from querying the database
    # artist_list = Artist.query.with_entities(Artist.id, Artist.name)
    artist_list = Artist.query.all()
    artist_dic = {}
    data = []
    for artist in artist_list:
        artist_id = artist.id
        print(artist_id)
        name = artist.name
        if artist_id not in artist_dic:
            artist_dic[artist_id] = {"id": artist_id, "name": name}
    for artist_id in artist_dic.keys():
        data.append(dict(id=artist_id, name=artist_dic[artist_id]["name"]))

    print(data)

    return render_template("pages/artists.html", artists=data)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # search for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get("search_term", "")
    searched_artists = (
        db.session.query(Artist)
        .filter(func.lower(Artist.name).ilike(f"%{search_term}%"))
        .all()
    )
    response = {"count": len(searched_artists), "data": []}
    for artist in searched_artists:
        response["data"].append(
            {
                "id": artist.id,
                "name": artist.name,
                "num_upcoming_shows": (
                    db.session.query(func.count(Show.id))
                    .filter(Show.artist_id == artist.id)
                    .filter(Show.start_time > datetime.now())
                    .scalar()
                ),
            }
        )
    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    artist = Artist.query.filter(Artist.id == artist_id).first()
    past_shows = (
        db.session.query(Show, Venue)
        .join(Venue, Show.venue_id == Venue.id)
        .filter(Show.artist_id == artist_id)
        .filter(Show.start_time < datetime.now())
        .all()
    )

    upcoming_shows = (
        db.session.query(Show, Venue)
        .join(Venue, Show.venue_id == Venue.id)
        .filter(Show.artist_id == artist_id)
        .filter(Show.start_time > datetime.now())
        .all()
    )

    past = []
    for show, venue in past_shows:
        past.append(
            {
                "venue_id": venue.id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": str(show.start_time),
            }
        )

    upcoming = []
    for show, venue in upcoming_shows:
        upcoming.append(
            {
                "venue_id": venue.id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": str(show.start_time),
            }
        )

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "image_link": artist.image_link,
        "past_shows": past,
        "upcoming_shows": upcoming,
        "past_show_count": len(past),
        "upcoming_shows_count": len(upcoming),
    }

    return render_template("pages/show_artist.html", artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.filter(Artist.id == artist_id).first()
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    artist = Artist.query.filter(Artist.id == artist_id).first()
    form = ArtistForm(request.form, meta={"csrf": False})
    if form.validate():
        try:
            artist.name = form.name.data
            artist.city = form.city.data
            artist.state = form.state.data
            artist.phone = form.phone.data
            artist.genres = form.genres.data
            artist.image_link = form.image_link.data
            artist.website_link = form.website_link.data
            artist.facebook_link = form.facebook_link.data
            artist.seeking_venue = form.seeking_venue.data
            artist.seeking_description = form.seeking_description.data
            db.session.commit()
        except Exception as e:
            print("Error occurred:", e)
            db.session.rollback()
        finally:
            db.session.close()
            return redirect(url_for("show_artist", artist_id=artist_id))
    else:
        return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.filter(Venue.id == venue_id).first()
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    venue = Venue.query.filter(Venue.id == venue_id).first()
    form = VenueForm(request.form, meta={"csrf": False})
    if form.validate():
        try:
            venue.name = form.name.data
            venue.city = form.city.data
            venue.state = form.state.data
            venue.address = form.address.data
            venue.phone = form.phone.data
            venue.genres = form.genres.data
            venue.image_link = form.image_link.data
            venue.website_link = form.website_link.data
            venue.facebook_link = form.facebook_link.data
            venue.seeking_talent = form.seeking_talent.data
            venue.seeking_description = form.seeking_description.data

            db.session.commit()
        except:
            db.session.rollback()
        finally:
            db.session.close()

        return redirect(url_for("show_venue", venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = ArtistForm(request.form, meta={"csrf": False})
    if form.validate():
        try:
            artist = Artist(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                phone=form.phone.data,
                image_link=form.image_link.data,
                facebook_link=form.facebook_link.data,
                seeking_description=form.seeking_description.data,
                seeking_venue=form.seeking_venue.data,
                genres=form.genres.data,
                website=form.website_link.data,
            )

            db.session.add(artist)
            db.session.commit()
            flash("Artist " + request.form["name"] + " was successfully listed!")
        except Exception as e:
            flash(
                "An error occurred. Artist "
                + request.form["name"]
                + " could not be listed."
            )
            print(e)
            db.session.rollback()
        finally:
            db.session.close()
    else:
        message = []
        for field, err in form.errors.items():
            message.append(field + " " + "|".join(err))
        flash("Errors " + str(message))
        form = ArtistForm()
        return render_template("forms/new_artist.html", form=form)
    return render_template("pages/home.html")

    # on successful db insert, flash success
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    shows_list = db.session.query(Show).all()
    final_shows = []

    for show in shows_list:
        final_shows.append(
            {
                "venue_id": show.venue_id,
                "venue_name": Venue.query.filter(show.venue_id == Venue.id)
                .first()
                .name,
                "artist_id": show.artist_id,
                "artist_name": Artist.query.filter(show.artist_id == Artist.id)
                .first()
                .name,
                "artist_image_link": Artist.query.filter(show.artist_id == Artist.id)
                .first()
                .image_link,
                "start_time": format_datetime(str(show.start_time)),
            }
        )
    return render_template("pages/shows.html", shows=final_shows)


@app.route("/shows/create")
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    form = ShowForm(request.form, meta={"csrf": False})
    if form.validate():
        show = Show(
            artist_id=form.artist_id.data,
            venue_id=form.venue_id.data,
            start_time=form.start_time.data,
        )
        try:
            db.session.add(show)
            db.session.commit()
            flash("Show was successfully listed!")
        except Exception as e:
            db.session.rollback()
            flash("An error occurred. Show could not be listed.")
            print(e)  # print the error message to the console for debugging purposes
        finally:
            db.session.close()
    else:
        message = []
        for field, err in form.errors.items():
            message.append(field + " " + "|".join(err))
        flash("Errors " + str(message))
        form = ShowForm()
        return render_template("forms/new_show.html", form=form)
    return render_template("pages/home.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
