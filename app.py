#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, abort, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from config import csrf
from flask_migrate import Migrate
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    genres = db.Column(db.ARRAY(db.String()))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String())
    shows = db.relationship('Show', backref='Venue', lazy=False)

    def __repr__(self):
      return f'<Venue: {self.id}, name: {self.name}, phone: {self.phone}'

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String())
    shows = db.relationship('Show', backref='Artist', lazy=False)

    def __repr__(self):
      return f'<Artist: {self.id}, name: {self.name}, phone: {self.phone}'

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
  __tablename__ = 'Show'
  id = db.Column(db.Integer, primary_key=True)
  start_time = db.Column(db.DateTime)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)

  def __repr__(self):
      return f'<Show: {self.id}, artist_id: {self.artist_id}, venue_id:{self.venue_id}, date: {self.start_time}'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  res = []
  venue_query = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state)

  for venue in venue_query:
    item_query = Venue.query.filter(Venue.state == venue.state).filter(Venue.city == venue.city).all()
    data = []

    for item in item_query:
      data.append({
        'id': item.id,
        'name': item.name,
        'num_upcoming_shows': len(db.session.query(Show).filter(Show.start_time > datetime.now()).all())
      })

      res.append({
        'city': venue.city,
        'state': venue.state,
        'venues': data
      })

  return render_template('pages/venues.html', areas=res) 

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # search for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term', '')
  search_format = f'%{search_term}%'

  search = db.session.query(Venue).filter(Venue.name.ilike(search_format)).all()
  response = {
     'count':len(search),
     'data': search
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

  data = Venue.query.filter_by(id=venue_id).first()
  data.website = data.website_link

  upcoming_shows = []
  past_shows = []

  for show in data.shows:
    if show.start_time > datetime.now():
      upcoming_shows.append(show)
    else:
      past_shows.append(show)
      
  data.upcoming_shows = upcoming_shows
  data.past_shows = past_shows

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  app = Flask(__name__)
  csrf.init_app(app)

  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  app = Flask(__name__)
  csrf.init_app(app)

  try:
    venue = Venue(
      name = request.form['name'],
      city = request.form['city'],
      state = request.form['state'],
      address = request.form['address'],
      phone = request.form['phone'],
      image_link = request.form['image_link'],
      facebook_link = request.form['facebook_link'],
      genres = request.form.getlist('genres'),
      website_link = request.form['website_link'],
      seeking_talent = bool(request.form.get('seeking_talent', False)),
      seeking_description = request.form['seeking_description'],
    )

    db.session.add(venue)
    db.session.commit()

    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully created!')
  except Exception as e:
    db.session.rollback()

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be created.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    print(sys.exc_info())
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be created.')
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    Venue.query.filter(Venue.id == venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = Artist.query.order_by('name').all()
  
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # search for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term','')
  search_format = f'%{search_term}'
  data = db.session.query(Artist).filter(Artist.name.ilike(search_format)).all()

  response = {
    'count': len(data),
    'data': data
  }

  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  data = Artist.query.filter_by(id=artist_id).first()
  data.website = data.website_link
  upcoming_shows = []
  past_shows = []

  for show in data.shows:
    if show.start_time > datetime.now():
      upcoming_shows.append(show)
    else:
      past_shows.append(show)

  data.upcoming_shows = upcoming_shows
  data.past_shows = past_shows

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  app = Flask(__name__)
  csrf.init_app(app)

  # TODO: populate form with fields from artist with ID <artist_id>
  form = ArtistForm()
  artist = Artist.query.filter_by(id=artist_id).first()

  form.name.data = artist.name
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.genres.data = artist.genres
  form.image_link.data = artist.image_link
  form.facebook_link.data = artist.facebook_link
  form.website_link.data = artist.website_link
  form.seeking_venue.data = bool(artist.seeking_venue)
  form.seeking_description.data = artist.seeking_description

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  app = Flask(__name__)
  csrf.init_app(app)

  try:
    artist = Artist.query.filter_by(id=artist_id).first()
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.website_link = request.form['website_link']
    artist.seeking_venue = bool(request.form.get('seeking_venue',False))
    artist.seeking_description = request.form['seeking_description']
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully edited!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be edited.')
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # TODO: populate form with values from venue with ID <venue_id>
  form = VenueForm()
  venue = Venue.query.filter_by(id=venue_id).first()

  form.name.data = venue.name
  form.city.data = venue.city
  form.state.data = venue.state
  form.address.data = venue.address
  form.phone.data = venue.phone
  form.image_link.data = venue.image_link
  form.facebook_link.data = venue.facebook_link
  form.genres.data = venue.genres
  form.website_link.data = venue.website_link 
  form.seeking_talent.data = bool(venue.seeking_talent)
  form.seeking_description.data = venue.seeking_description 

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  app = Flask(__name__)
  csrf.init_app(app)

  try:
    venue = Venue.query.filter_by(id=venue_id).first()
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.genres = request.form.getlist('genres')
    venue.website_link = request.form['website_link']
    venue.seeking_talent = bool(request.form.get('seeking_talent', False))
    venue.seeking_description = request.form['seeking_description']

    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully edited!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be edited.')
  finally:
    db.session.close()
  
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  app = Flask(__name__)
  csrf.init_app(app)

  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  app = Flask(__name__)
  csrf.init_app(app)

  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  try:
    artist = Artist(
      name = request.form['name'],
      city = request.form['city'],
      state = request.form['state'],
      phone = request.form['phone'],
      genres = request.form.getlist('genres'),
      image_link = request.form['image_link'],
      facebook_link = request.form['facebook_link'],
      website_link = request.form['website_link'],
      seeking_venue = bool(request.form.get('seeking_venue',False)),
      seeking_description = request.form['seeking_description']
    )

    db.session.add(artist)
    db.session.commit()  
    
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully created!')
  except Exception as e:
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be edited.')
    print(sys.exc_info())
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be created.')
    db.session.rollback()
  finally:
    db.session.close()

  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  shows = Show.query.all()
  data = []

  for show in shows:
    data.append({
      'start_time': show.start_time.isoformat(),
      'artist_id': show.artist_id,
      'venue_id': show.venue_id
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  app = Flask(__name__)
  csrf.init_app(app)

  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  try:
    show = Show(
      start_time = request.form['start_time'],
      artist_id = request.form['artist_id'],
      venue_id = request.form['venue_id'],
    )

    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully created!')
  except:
    db.session.rollback()
    print(sys.exc_info()) 
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be created.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Show could not be created.')  
  finally:
    db.session.close()
  
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

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
