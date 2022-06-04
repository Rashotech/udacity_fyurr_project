#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging 
from logging import Formatter, FileHandler
from models import db, Artist, Venue, Show
from forms import *
import os

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

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
  data=[]
  venues = Venue.query.distinct(Venue.city, Venue.state).all()
  if venues:
    for venue in venues:
      venueInfo = []
      for v in Venue.query.filter_by(city=venue.city, state=venue.state).all():
        venueInfo.append({
          "id": v.id,
          "name": v.name,
          "num_upcoming_shows": len(Venue.query.join(Show).filter(Show.start_time > datetime.utcnow(),
                                             Show.venue_id == venue.id).all())
        })
      data.append({
        "city": venue.city,
        "state": venue.state,
        "venues": venueInfo
      }) 
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  data = []
  search_string = request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike(f"%{search_string}%")).all()

  for venue in venues:
      data.append({
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": len(Venue.query.join(Show).filter(Show.start_time > datetime.utcnow(), 
                                          Show.venue_id == venue.id).all())
      })
      
  count_venues = len(venues)
  search_result = {
      "count": count_venues,
      "data": data
  }

  return render_template('pages/search_venues.html', results=search_result, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)

  if venue is None:
      abort(404)

  shows = Show.query.filter_by(venue_id=venue_id).all()
  artist_upcoming_shows = []
  artist_past_shows = []

  for show in shows:
    start_time = format_datetime(str(show.start_time))
    artist_show = {
        "artist_id": show.artist.id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": start_time
    }
    if show.start_time >= datetime.utcnow():
        artist_upcoming_shows.append(artist_show)
    else:
        artist_past_shows.append(artist_show)

  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres.split(','),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "upcoming_shows": artist_upcoming_shows,
    "upcoming_shows_count": len(artist_upcoming_shows),
    "past_shows": artist_past_shows,
    "past_shows_count": len(artist_past_shows),
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
  venue_form_input = VenueForm()

  if venue_form_input.validate_on_submit():
    try: 
      created_venue = Venue(
        name=venue_form_input.name.data,
        genres= ','.join(venue_form_input.genres.data),
        address=venue_form_input.address.data,
        city=venue_form_input.city.data,
        state=venue_form_input.state.data,
        phone=venue_form_input.phone.data,
        facebook_link=venue_form_input.facebook_link.data,
        image_link=venue_form_input.image_link.data,
        website=venue_form_input.website_link.data,
        seeking_talent=venue_form_input.seeking_talent.data,
        seeking_description=venue_form_input.seeking_description.data
      )
        
      db.session.add(created_venue)
      db.session.commit()

      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:        
        db.session.rollback()
          # On unsuccessful db insert, flash an error instead.
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()       
  else:
    return render_template('forms/new_venue.html', form=venue_form_input)
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except Exception as e:
    print(e)
    db.session.rollback()
  finally:
    db.session.close()
  return jsonify({ 'success': True })

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data=[]
  artists = Artist.query.with_entities(Artist.id, Artist.name).all()
  if artists:
    for artist in artists:
      data.append({
        "id": artist.id,
        "name": artist.name,
      }) 
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  data = []
  search_string = request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike(f"%{search_string}%")).all()

  for artist in artists:
      data.append({
          "id": artist.id,
          "name": artist.name,
          "num_upcoming_shows": len(Venue.query.join(Show).filter(Show.start_time > datetime.utcnow(), 
                                          Show.artist_id == artist.id).all())
      })
      
  count_artists = len(artists)
  search_result = {
      "count": count_artists,
      "data": data
  }
  return render_template('pages/search_artists.html', results=search_result, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)

  if artist is None:
    abort(404)

  shows = Show.query.filter_by(artist_id=artist_id).all()
  venue_upcoming_shows = []
  venue_past_shows = []

  for show in shows:
    start_time = format_datetime(str(show.start_time))
    venue_show = {
        "venue_id": show.venue.id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": start_time
    }
    if show.start_time >= datetime.utcnow():
      venue_upcoming_shows.append(venue_show)
    else:
      venue_past_shows.append(venue_show)

  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres.split(','),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "upcoming_shows": venue_upcoming_shows,
    "upcoming_shows_count": len(venue_upcoming_shows),
    "past_shows": venue_past_shows,
    "past_shows_count": len(venue_past_shows)
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  form.name.data = artist.name
  form.genres.data = artist.genres.split(',')
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.website_link.data = artist.website
  form.image_link.data = artist.image_link
  form.facebook_link.data = artist.facebook_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  
  if form.validate_on_submit():
    try:
      artist.name = form.name.data
      artist.genres = ','.join(form.genres.data)
      artist.city = form.city.data
      artist.state = form.state.data
      artist.phone = form.phone.data
      artist.website = form.website_link.data
      artist.facebook_link = form.facebook_link.data
      artist.image_link = form.image_link.data
      artist.seeking_venue = form.seeking_venue.data
      artist.seeking_description = form.seeking_description.data

      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully updated!')
    except:
      db.session.rollback()
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    finally:
      db.session.close()
  else:
    return render_template('forms/edit_artist.html', form=form, artist=artist)
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  form.name.data = venue.name
  form.genres.data = venue.genres.split(',')
  form.city.data = venue.city
  form.state.data = venue.state
  form.address.data = venue.address
  form.phone.data = venue.phone
  form.website_link.data = venue.website
  form.image_link.data = venue.image_link
  form.facebook_link.data = venue.facebook_link
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  
  if form.validate_on_submit():
    try:
      venue.name = form.name.data
      venue.genres = ','.join(form.genres.data)
      venue.city = form.city.data
      venue.state = form.state.data
      venue.phone = form.phone.data
      venue.address = form.address.data
      venue.website = form.website_link.data
      venue.facebook_link = form.facebook_link.data
      venue.image_link = form.image_link.data
      venue.seeking_talent = form.seeking_talent.data
      venue.seeking_description = form.seeking_description.data

      db.session.commit()

      flash('Venue ' + request.form['name'] + ' was successfully updated!')
    except:
      db.session.rollback()
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
    finally:
      db.session.close()
  else:
    return render_template('forms/edit_venue.html', form=form, venue=venue)
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  artist_form_input = ArtistForm()
  # Validate form input
  if artist_form_input.validate_on_submit():
    try: 
      created_artist = Artist(
        name=artist_form_input.name.data,
        genres= ','.join(artist_form_input.genres.data),
        city=artist_form_input.city.data,
        state=artist_form_input.state.data,
        phone=artist_form_input.phone.data,
        facebook_link=artist_form_input.facebook_link.data,
        image_link=artist_form_input.image_link.data,
        website=artist_form_input.website_link.data,
        seeking_venue=artist_form_input.seeking_venue.data,
        seeking_description=artist_form_input.seeking_description.data
      )
        
      db.session.add(created_artist)
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except Exception as e:
        print(e)      
        db.session.rollback()
          # On unsuccessful db insert, flash an error instead.
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()    
  else:
    return render_template('forms/new_artist.html', form=artist_form_input)
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = []
  data = Show.query.all()

  for show in data:
    start_time = format_datetime(str(show.start_time))
    shows.append({
      'venue_id': show.venue_id,
      'venue_name': show.venue.name,
      'artist_id': show.artist_id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      "start_time": start_time
    })

  return render_template("pages/shows.html", shows=shows)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  show_form_input = ShowForm()

  if show_form_input.validate_on_submit():
    try:
      created_show = Show(
          artist_id=show_form_input.artist_id.data,
          venue_id=show_form_input.venue_id.data,
          start_time=show_form_input.start_time.data
      )
      db.session.add(created_show)
      db.session.commit()

      # on successful db insert, flash success
      flash('Show was successfully listed!')
    except:     
      db.session.rollback()
        # On unsuccessful db insert, flash an error instead.
      flash('An error occurred. Show could not be listed.')
    finally:
      db.session.close()           
  else:
    return render_template('forms/new_show.html', form=show_form_input)
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(405)
def not_found_error(error):
    return render_template('errors/500.html'), 405

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
# if __name__ == '__main__':
#     app.run()

# Or specify port manually:
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
