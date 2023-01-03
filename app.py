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
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy.sql.functions import now, func

from forms import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# TODO: connect to a local postgresql database

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    website = db.Column(db.String(120))
    shows = db.relationship('Show', backref='venue', lazy=True)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))
    website = db.Column(db.String(120))
    shows = db.relationship('Show', backref='artist', lazy=True)


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=now(), nullable=False)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
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
            data[city] = {
                "state": state,
                "venues": []
            }
        data[city]["venues"].append({
            "id": area.id,
            "name": area.name,
            "num_upcoming_shows": (db.session.query(func.count(Show.id))
                                   .filter(Show.venue_id == Venue.id)
                                   .filter(Show.start_time > datetime.now())
                                   .scalar())
        })
    for city in data.keys():
        final_areas.append(dict(city=city, state=data[city]["state"], venues=data[city]["venues"]))

    return render_template('pages/venues.html', areas=final_areas)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # search for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term', '')
    searched_venues = db.session.query(Venue).filter(func.lower(Venue.name).ilike(search_term)).all()
    response = {
        "count": len(searched_venues),
        "data": []
    }
    for venue in searched_venues:
        response["data"].append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": (db.session.query(func.count(Show.id))
                                   .filter(Show.venue_id == venue.id)
                                   .filter(Show.start_time > datetime.now())
                                   .scalar())
        })

    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.filter(Venue.id == venue_id).first()
    past_shows = (db.session.query(Show, Artist)
                  .join(Artist, Show.artist_id == Artist.id)
                  .filter(Show.venue_id == venue_id)
                  .filter(Show.start_time < datetime.now()).all())
    upcoming_shows = (db.session.query(Show, Artist)
                      .join(Artist, Show.artist_id == Artist.id)
                      .filter(Show.venue_id == venue_id)
                      .filter(Show.start_time > datetime.now()).all())

    past = []
    for show, artist in past_shows:
        past.append({
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": str(show.start_time)
        })

    upcoming = []
    for show, artist in upcoming_shows:
        upcoming.append({
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": str(show.start_time)
        })

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
        "upcoming_shows_count": len(upcoming)
    }
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        address = request.form['address']
        phone = request.form['phone']
        image_link = request.form['image_link']
        facebook_link = request.form['facebook_link']
        seeking_talent = "false"
        try:
            seeking_talent = request.get_json()['seeking_talent']
        except Exception as e:
            print('failed but all good', e)
        print(seeking_talent)
        seeking_description = request.form.get('seeking_description', '')
        genres = request.form.getlist('genres')
        website = request.form['website_link']
        talent = False
        if seeking_talent == "y":
            talent = True

        venue = Venue(name=name, city=city, state=state,
                      address=address, phone=phone, image_link=image_link,
                      facebook_link=facebook_link, seeking_talent=talent,
                      seeking_description=seeking_description,
                      genres=genres, website=website)

        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except Exception as e:
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
        print(e)
        db.session.rollback()
    finally:
        db.session.close()
        return render_template('pages/home.html')

    # on successful db insert, flash success
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/


@app.route('/venues/<venue_id>', methods=['DELETE'])
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
@app.route('/artists')
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
            artist_dic[artist_id] = {
                "id": artist_id,
                "name": name
            }
    for artist_id in artist_dic.keys():
        data.append(dict(id=artist_id, name=artist_dic[artist_id]["name"]))

    print(data)

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # search for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '')
    searched_artists = db.session.query(Artist).filter(func.lower(Artist.name).ilike(search_term)).all()
    response = {
        "count": len(searched_artists),
        "data": []
    }
    for artist in searched_artists:
        response["data"].append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": (db.session.query(func.count(Show.id))
                                   .filter(Show.artist_id == artist.id)
                                   .filter(Show.start_time > datetime.now())
                                   .scalar())
        })
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    artist = Artist.query.filter(Artist.id == artist_id).first()
    past_shows = (db.session.query(Show, Venue)
                  .filter(Show.artist_id == artist_id)
                  .filter(Show.start_time < datetime.now()).all())
    upcoming_shows = (db.session.query(Show, Venue)
                      .filter(Show.artist_id == artist_id)
                      .filter(Show.start_time > datetime.now()).all())

    for s, v in db.session.query(Show, Venue).filter(Show.artist_id == artist_id).all():
        print("ID: {} Name: {} Invoice No: {} Amount: {}".format(v.id, v.name, s.artist_id, s.venue_id))

    past = []
    for show, venue in past_shows:
        past.append({
            "venue_id": show.venue_id,
            "venue_name": venue.name,
            "venue_image_link": venue.image_link,
            "start_time": str(show.start_time)
        })

    upcoming = []
    for show in upcoming_shows:
        upcoming.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue_name,
            "venue_image_link": show.venue_image_link,
            "start_time": str(show.start_time)
        })

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
        "upcoming_shows_count": len(upcoming)
    }

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.filter(Artist.id == artist_id).first()
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    artist = Artist.query.filter(Artist.id == artist_id).first()
    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        phone = request.form['phone']
        image_link = request.form['image_link']
        facebook_link = request.form['facebook_link']
        seeking_description = request.form.get('seeking_description', '')
        seeking_venue = "false"
        try:
            seeking_venue = request.get_json()['seeking_venue']
        except Exception as e:
            print('failed but all good', e)
        genres = request.form.getlist('genres')
        website = request.form['website_link']
        venue = False
        if seeking_venue == "y":
            venue = True

        artist.name = name
        artist.city = city
        artist.state = state
        artist.phone = phone
        artist.genres = genres
        artist.image_link = image_link
        artist.website = website
        artist.facebook_link = facebook_link
        artist.seeking_venue = venue
        artist.seeking_description = seeking_description

        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.filter(Venue.id == venue_id).first()
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    venue = Venue.query.filter(Venue.id == venue_id).first()
    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        address = request.form['address']
        phone = request.form['phone']
        image_link = request.form['image_link']
        facebook_link = request.form['facebook_link']
        seeking_talent = "false"
        try:
            seeking_talent = request.get_json()['seeking_talent']
        except Exception as e:
            print('failed but all good', e)
        print(seeking_talent)
        seeking_description = request.form.get('seeking_description', '')
        genres = request.form.getlist('genres')
        website = request.form['website_link']
        talent = False
        if seeking_talent == "y":
            talent = True

        venue.name = name
        venue.city = city
        venue.state = state
        venue.address = address
        venue.phone = phone
        venue.image_link = image_link
        venue.facebook_link = facebook_link
        venue.seeking_talent = talent
        venue.seeking_description = seeking_description
        venue.genres = genres
        venue.website = website

        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        phone = request.form['phone']
        image_link = request.form['image_link']
        facebook_link = request.form['facebook_link']
        seeking_description = request.form.get('seeking_description', '')
        seeking_venue = request.form['seeking_venue']
        genres = request.form.getlist('genres')
        website = request.form['website_link']
        seeking = False
        if seeking_venue == "y":
            seeking = True

        artist = Artist(name=name, city=city, state=state,
                        phone=phone, image_link=image_link,
                        facebook_link=facebook_link, seeking_venue=seeking,
                        seeking_description=seeking_description,
                        genres=genres, website=website)

        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except Exception as e:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
        print(e)
        db.session.rollback()
    finally:
        db.session.close()
        return render_template('pages/home.html')

    # on successful db insert, flash success
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    shows_list = (db.session.query(Show).all())
    final_shows = []

    for show in shows_list:
        final_shows.append({
            "venue_id": show.venue_id,
            "venue_name": Venue.query.filter(show.venue_id == Venue.id).first().name,
            "artist_id": show.artist_id,
            "artist_name": Artist.query.filter(show.artist_id == Artist.id).first().name,
            "artist_image_link": Artist.query.filter(show.artist_id == Artist.id).first().image_link,
            "start_time": format_datetime(str(show.start_time))
        })
    return render_template('pages/shows.html', shows=final_shows)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    try:
        artist_id = request.form['artist_id']
        venue_id = request.form['venue_id']
        start_time = datetime.strptime(request.form['start_time'], '%Y-%m-%d %H:%M:%S')

        show = Show(artist_id=artist_id, venue_id=venue_id,  start_time=start_time)

        db.session.add(show)
        db.session.commit()
    except:
        db.session.rollback()
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()
        flash('Show was successfully listed!')
    # on successful db insert, flash success
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
