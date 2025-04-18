"""
Flask Documentation:     https://flask.palletsprojects.com/
Jinja2 Documentation:    https://jinja.palletsprojects.com/
Werkzeug Documentation:  https://werkzeug.palletsprojects.com/
This file creates your application.
"""

from app import app, db
from flask import render_template, request, jsonify, send_file
from .forms import MovieForm
from .models import Movie
from datetime import datetime
import os
from flask_wtf.csrf import generate_csrf  # Add this import at the top


###
# Routing for your application.
###

@app.route('/')
def index():
    return jsonify(message="This is the beginning of our API")


# Add the CSRF token route here
@app.route('/api/v1/csrf-token', methods=['GET'])
def get_csrf():
    return jsonify({'csrf_token': generate_csrf()})


###
# The functions below should be applicable to all Flask apps.
###

# Here we define a function to collect form errors from Flask-WTF
# which we can later use
def form_errors(form):
    error_messages = []
    """Collects form errors"""
    for field, errors in form.errors.items():
        for error in errors:
            message = u"Error in the %s field - %s" % (
                    getattr(form, field).label.text,
                    error
                )
            error_messages.append(message)

    return error_messages

@app.route('/<file_name>.txt')
def send_text_file(file_name):
    """Send your static text file."""
    file_dot_text = file_name + '.txt'
    return app.send_static_file(file_dot_text)

# Route for handling movies - supports both GET and POST
@app.route('/api/v1/movies', methods=['GET', 'POST'])
def movies():
    if request.method == 'GET':
        movies = Movie.query.all()
        movies_list = []
        
        for movie in movies:
            movies_list.append({
                'id': movie.id,
                'title': movie.title,
                'description': movie.description,
                'poster': f'/api/v1/posters/{movie.poster}'
            })
        
        return jsonify({'movies': movies_list})
    
    elif request.method == 'POST':
        form = MovieForm()

        if form.validate_on_submit():
            #Save the uploaded file
            poster_file = form.poster.data
            poster_filename = poster_file.filename
            poster_path = os.path.join(app.config['UPLOAD_FOLDER'], poster_filename)
            poster_file.save(poster_path)

            #Create a new Movie Instance
            new_movie = Movie(
                title = form.title.data,
                description = form.description.data,
                poster=poster_filename,
                created_at=datetime.now()
            )

            #Add the movie to the database
            db.session.add(new_movie)
            db.session.commit()

            #Return a success message
            return jsonify({
                "message": "Movie Successfully added",
                "title": new_movie.title,
                "poster": new_movie.poster,
                "description": new_movie.description
            }), 201
        else:
            #Collect Form Errors
            errors = form_errors(form)
            return jsonify({"errors": errors}), 400

# Route to serve poster images
@app.route('/api/v1/posters/<filename>', methods=['GET'])
def get_image(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also tell the browser not to cache the rendered page. If we wanted
    to we could change max-age to 600 seconds which would be 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 page."""
    return render_template('404.html'), 404