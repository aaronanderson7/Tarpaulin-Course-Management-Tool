# Name: Aaron Anderson
# Class: CS493
# Assignment: 6
# Name: Tarpaulin Course Management Tool.
# Due Date: 06/07/2024 (turning in on 06/08/2024 for a penalty. )

from flask import Flask, request, jsonify, send_file
from google.cloud import datastore
from google.cloud import storage
import requests
import json
import io
from six.moves.urllib.request import urlopen
from jose import jwt
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = 'SECRET_KEY'

# Datastore Client. 
client = datastore.Client()

# Declare global url variables
PHOTO_BUCKET = 'tarpaulin'
USERS = 'users'
LOGIN = 'login'
AVATAR = 'avatar'
COURSES = 'courses'
STUDENTS = 'students'
ENROLLMENT = 'enrollment'

# Update the values of the following 3 variables
CLIENT_ID = '408UgvzHEmYd00iTDmyKqr5xtGyUwsty'
CLIENT_SECRET = 'YeNRHN6eUQzq7JwbGVUyRtVCLsBiW3QNL_myc0_A3iIZDBtodlXwKj9FPECa5RGr'
DOMAIN = 'dev-houfkps8jvrd1ooa.us.auth0.com'
# For example
# DOMAIN = '493-24-spring.us.auth0.com'
# Note: don't include the protocol in the value of the variable DOMAIN

ALGORITHMS = ["RS256"]

oauth = OAuth(app)

auth0 = oauth.register(
    'auth0',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    api_base_url="https://" + DOMAIN,
    access_token_url="https://" + DOMAIN + "/oauth/token",
    authorize_url="https://" + DOMAIN + "/authorize",
    client_kwargs={
        'scope': 'openid profile email',
    },
)

# This code is adapted from https://auth0.com/docs/quickstart/back
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

# Verify the JWT in the request's Authorization header
def verify_jwt(request):
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization'].split()
        token = auth_header[1]
    else:
        raise AuthError({"Error": "Unauthorized"}, 401)
    
    jsonurl = urlopen("https://"+ DOMAIN+"/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise AuthError({"Error": "Unauthorized"}, 401)
    if unverified_header["alg"] == "HS256":
        raise AuthError({"Error": "Unauthorized"}, 401)
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=CLIENT_ID,
                issuer="https://"+ DOMAIN+"/"
            )
        except jwt.ExpiredSignatureError:
            raise AuthError({"Error": "Unauthorized"}, 401)
        except jwt.JWTClaimsError:
            raise AuthError({"Error": "Unauthorized"}, 401)
        except Exception:
            raise AuthError({"Error": "Unauthorized"}, 401)

        return payload
    else:
        raise AuthError({"Error": "Unauthorized"}, 401)



# Home Page - DONE
@app.route('/')
def index():
    return "Welcome to the Tarpaulin Course Management Tool."



# Decode the JWT supplied in the Authorization header - DONE
@app.route('/decode', methods=['GET'])
def decode_jwt():
    payload = verify_jwt(request)
    return payload    



# Generate a JWT from the Auth0 domain and return it
# Request: JSON body with 2 properties with "username" and "password"
#       of a user registered with this Auth0 domain
# Response: JSON with the JWT as the value of the property id_token
# DONE
@app.route('/' + USERS + '/' + LOGIN, methods=['POST'])
def login_user():
    content = request.get_json()
    # Error handling for incorrect body. 
    request_list = ['username', 'password']
    for attribute in request_list:
        if attribute not in content:
            return {"Error": "The request body is invalid"}, 400
    username = content["username"]
    password = content["password"]
    body = {'grant_type':'password','username':username,
            'password':password,
            'client_id':CLIENT_ID,
            'client_secret':CLIENT_SECRET
           }
    headers = { 'content-type': 'application/json' }
    url = 'https://' + DOMAIN + '/oauth/token'
    r = requests.post(url, json=body, headers=headers)
    if r.status_code == 200:
        result = r.json()
        response = {
            "token": result["id_token"]
        }
        return response, 200, {'Content-Type': 'application/json'}
    else:
        return {"Error": "Unauthorized"}, 401
    

# Get all users - but only users with admin role can acccess all the users. 
# DONE
@app.route('/' + USERS, methods=['GET'])
def get_users():
    if request.method == 'GET':
        payload = verify_jwt(request)
        sub = payload["sub"]
        
        # index datastore entries to find matching "admin" sub
        query = client.query(kind=USERS)
        query.add_filter('sub', '=', sub)
        results = list(query.fetch())
        if len(results) == 0:
            return {"Error": "Unauthorized"}, 401
        admin = False
        for r in results:
            if r["sub"] == sub:
                if r["role"] == "admin":
                    admin = True
                else:
                    return {"Error": "You don't have permission on this resource"}, 403

        if admin:
            query = client.query(kind=USERS)
            results = list(query.fetch())
            for r in results:
                r['id'] = r.key.id
            return results
        else:
            return {"Error": "Unauthorized"}, 401
    else:
        return jsonify(error = "Method not recognized")



# Get a specific user
# 1. If there is a avatar_url - must include.
# 2. If role is "instructor" or "student" must include property courses.
@app.route('/' + USERS + '/<int:id>', methods=['GET'])
def get_user(id):
    if request.method == 'GET':
        # Verify JWT first
        payload = verify_jwt(request)
        sub = payload["sub"]

        # Verify the User - either admin or JWT owner
        user_key = client.key(USERS, id)
        user = client.get(key=user_key)
        if user["role"] != "admin":
            if user["sub"] != sub:
                return {"Error": "You don't have permission on this resource"}, 403
        
        # Proceed to Get User Information
        # First check if there is an avatar
        query = client.query(kind=AVATAR)
        query.add_filter('user_id', '=', id)
        results = list(query.fetch())
        if len(results) != 0:
            user["avatar_url"] = request.host_url + USERS + '/' + str(id) + '/' + AVATAR

        # Second check the role. 
        if user["role"] == "instructor":
            query = client.query(kind=COURSES)
            query.add_filter('instructor_id', '=', user.key.id)
            results = list(query.fetch())
            user["courses"] = []
            for course in results:
                user["courses"].append(request.host_url + COURSES + '/' + str(course.key.id))
        
        if user["role"] == "student":
            query = client.query(kind=ENROLLMENT)
            query.add_filter('student_id', '=', user.key.id)
            results = list(query.fetch())
            user["courses"] = []
            for enrollment in results:
                user["courses"].append(request.host_url + COURSES + '/' + str(enrollment["course_id"]))
        
        # return the response
        user["id"] = user.key.id
        return user

    else:
        return jsonify(error = "Method not recognized")



# Create / Upload user's avatar - DONE
@app.route('/' + USERS + '/<int:id>' + '/' + AVATAR, methods=['POST'])
def post_avatar(id):
    if request.method == 'POST':
        # First check if file is in request
        if "file" not in request.files:
            return {"Error": "The request body is invalid"}, 400
        file_obj = request.files['file']

        # Second check for validity of JWT / id - matching. 
        payload = verify_jwt(request)         
        user_key = client.key(USERS, id)
        user = client.get(key = user_key)
        if user is None:
            return {"Error": "You don't have permission on this resource"}, 403
        if user["sub"] != payload["sub"]:
            return {"Error": "You don't have permission on this resource"}, 403

        
        # Using a separate avatar datastore - check if the user_id has an avatar. 
        query = client.query(kind=AVATAR)
        query.add_filter('user_id', '=', id)
        results = list(query.fetch())
        if len(results) == 0:
            # Create a new avatar
            storage_client = storage.Client()
            bucket = storage_client.get_bucket(PHOTO_BUCKET)
            # Instead of using the file name - I will use the str(id) to keep track for future gets
            blob = bucket.blob(file_obj.filename)
            file_obj.seek(0)
            blob.upload_from_file(file_obj)
            new_avatar = datastore.Entity(key=client.key(AVATAR))
            new_avatar.update({
                "user_id": id,
                "avatar": str(file_obj.filename)

            })
            client.put(new_avatar)
            response = {
                "avatar_url": request.host_url + USERS + '/' + str(id) + '/' + AVATAR
            }
            return response, 200
        else:
            # Update a new avatar.
            # First delete old a
            avatar = results[0]
            avatar.update({
                "avatar": str(file_obj.filename)
            })
            client.put(avatar)

            filename = results[0]["avatar"]
            storage_client = storage.Client()
            bucket = storage_client.get_bucket(PHOTO_BUCKET)
            blob = bucket.blob(filename)
            blob.delete()
            # Then upload new one. 
            blob = bucket.blob(file_obj.filename)
            file_obj.seek(0)
            blob.upload_from_file(file_obj)
            response = {
                "avatar_url": request.host_url + USERS + '/' + str(id) + '/' + AVATAR
            }
            return response, 200

    else:
        return jsonify(error = "Method not recognized")



# GET user's avatar - DONE
@app.route('/' + USERS + '/<int:id>' + '/' + AVATAR, methods=['GET'])
def get_avatar(id):
    if request.method == 'GET':
        # Check for validity of JWT / id - matching. 
        payload = verify_jwt(request)         
        user_key = client.key(USERS, id)
        user = client.get(key = user_key)
        if user is None:
            return {"Error": "You don't have permission on this resource"}, 403
        if user["sub"] != payload["sub"]:
            return {"Error": "You don't have permission on this resource"}, 403
        query = client.query(kind=AVATAR)
        query.add_filter('user_id', '=', id)
        results = list(query.fetch())
        if len(results) == 0:
            return {"Error": "Not found"}, 404
        else:
            filename = results[0]["avatar"]
            storage_client = storage.Client()
            bucket = storage_client.get_bucket(PHOTO_BUCKET)
            blob = bucket.blob(filename)
            file_obj = io.BytesIO()
            blob.download_to_file(file_obj)
            file_obj.seek(0)
            return send_file(file_obj, mimetype='image/x-png', download_name=str(id))

    else:
        return jsonify(error = "Method not recognized")



# DELETE user's avatar - DONE
@app.route('/' + USERS + '/<int:id>' + '/' + AVATAR, methods=['DELETE'])
def delete_avatar(id):
    if request.method == 'DELETE':
        # Check for validity of JWT / id - matching. 
        payload = verify_jwt(request)         
        user_key = client.key(USERS, id)
        user = client.get(key = user_key)
        if user is None:
            return {"Error": "You don't have permission on this resource"}, 403
        if user["sub"] != payload["sub"]:
            return {"Error": "You don't have permission on this resource"}, 403
        
        query = client.query(kind=AVATAR)
        query.add_filter('user_id', '=', id)
        results = list(query.fetch())
        if len(results) == 0:
            return {"Error": "Not found"}, 404
        else:
            # First delete the avatar entry
            filename = results[0]["avatar"]
            avatar = results[0]
            avatar_key = client.key(AVATAR, avatar.key.id)
            client.delete(avatar_key)

            # Second delete the image from bucket
            storage_client = storage.Client()
            bucket = storage_client.get_bucket(PHOTO_BUCKET)
            blob = bucket.blob(filename)
            blob.delete()
            return ('', 204)

    else:
        return jsonify(error = "Method not recognized")




# Create a Course - DONE
# PROTETION - only users with admin role. 
@app.route('/' + COURSES, methods=['POST'])
def post_course():
    if request.method == 'POST':
        # Validate JWT
        payload = verify_jwt(request)
        sub = payload["sub"]
        query = client.query(kind=USERS)
        query.add_filter('sub', '=', sub)
        results = list(query.fetch())
        if len(results) == 0:
            return {"Error": "Unauthorized"}, 401
        admin = False
        for r in results:
            if r["sub"] == sub:
                if r["role"] == "admin":
                    admin = True
                else:
                    return {"Error": "You don't have permission on this resource"}, 403
        
        if admin:
            # Validate request body
            content = request.get_json()
            request_body = ['subject', 'number', 'title', 'term', 'instructor_id']
            for attribute in request_body:
                if attribute not in content:
                    return {"Error": "The request body is invalid"}, 400

            # Validate instructor_id
            instructor_id = content["instructor_id"]
            user_key = client.key(USERS, instructor_id)
            user = client.get(key = user_key)
            if user is None:
                return {"Error": "The request body is invalid"}, 400
            if user["role"] != "instructor":
                return {"Error": "The request body is invalid"}, 400
            else:
                new_course = datastore.entity.Entity(key = client.key(COURSES))
                new_course.update({
                    "subject": content["subject"],
                    "number": content["number"],
                    "title": content["title"],
                    "term": content["term"],
                    "instructor_id": content["instructor_id"]
                })
                client.put(new_course)
                new_course["id"] = new_course.key.id
                new_course["self"] = request.host_url + COURSES + '/' + str(new_course.key.id)
                return (jsonify(new_course), 201)

    else:
        return jsonify(error = "Method not recognized")


# Get all Courses - DONE
# - PROTECTION: None
# Pagination with limit/offset
# list must be sorted by the subject property. 
@app.route('/' + COURSES, methods = ['GET'])
def get_courses():
    if request.method == 'GET':
        # Grab the offset and limit - if they exist
        offset = request.args.get('offset')
        if offset is None:
            offset = 0
        else:
            offset = int(offset)
        
        limit = request.args.get('limit')
        if limit is None:
            limit = 3
        else:
            limit = int(limit)
        
        # get the courses 
        # Sort by subject + apply limit / offset
        query = client.query(kind=COURSES)
        query.order = ["subject"]
        c_iterator = query.fetch(limit=limit, offset=offset)
        pages = c_iterator.pages
        courses = list(next(pages))

        # Add the self and id to the courses.
        for course in courses:
            course["id"] = course.key.id
            course["self"] = request.host_url + COURSES + '/' + str(course.key.id)
        response = {
                "courses": courses,
                "next": request.host_url + COURSES + '?' + 'offset=' + str(offset + limit) + '&limit=3'
            }
        return response
    else:
        return jsonify(error = "Method not recognized")
        


# Get a course - DONE
# - PROTECTION: None
@app.route('/' + COURSES + '/<int:id>', methods = ['GET'])
def get_course(id):
    if request.method == 'GET':
        course_key = client.key(COURSES, id)
        course = client.get(key = course_key)
        if course is None:
            return {"Error": "Not found"}, 404
        else:
            course["id"] = course.key.id
            course["self"] = request.host_url + COURSES + '/' + str(id)
            return course
    
    else:
        return jsonify(error = "Method not recognized")


# Update a course
# - PROTECTION: only users with admin role.
@app.route('/' + COURSES + '/<int:id>', methods = ['PATCH'])
def update_course(id):
    if request.method == 'PATCH':
        # verify JWT and make sure that role is admin. 
        # Reworking my previous admin sorting to be more efficient. 
        payload = verify_jwt(request)
        sub = payload["sub"]
        query = client.query(kind=USERS)
        query.add_filter('sub', '=', sub)
        results = list(query.fetch())
        if len(results) == 0:
            return {"Error": "Unauthorized"}, 401
        else:
            # Get the course
            course_key = client.key(COURSES, id)
            course = client.get(key=course_key)
            if course is None:
                return {"Error": "You don't have permission on this resource"}, 403
            else:
                user = results[0]
                if user["role"] != "admin":
                    return {"Error": "You don't have permission on this resource"}, 403
                
                # Validate the content and input one by one. 
                content = request.get_json()
                if "instructor_id" in content:
                    user_key = client.key(USERS, int(content["instructor_id"]))
                    user = client.get(key = user_key)
                    if user is None:
                        return {"Error": "The request body is invalid"}, 400
                    if user["role"] != "instructor":
                        return {"Error": "The request body is invalid"}, 400
                    else:
                        # update instructor
                        course.update({
                            "instructor_id": content["instructor_id"]
                        })
                        client.put(course)
                if "subject" in content:
                    course.update({
                        "subject": content["subject"]
                    })
                    client.put(course)
                if "number" in content:
                    course.update({
                        "number": content["number"]
                    })
                    client.put(course)
                if "subject" in content:
                    course.update({
                        "subject": content["subject"]
                    })
                    client.put(course)
                if "term" in content:
                    course.update({
                        "term": content["term"]
                    })
                    client.put(course)
                if "title" in content:
                    course.update({
                        "title": content["title"]
                    })
                    client.put(course)
                course["id"] = course.key.id
                course["self"] = request.host_url + COURSES + '/' + str(id)
                return course
    else:
        return jsonify(error = "Method not recognized")



# Delete a course - IMPLEMENT DELETING ENROLLMENT ENTRIES
# - PROTECTION: Only admin users.
# - ALSO Deletes the enrollment of students

@app.route('/' + COURSES + '/<int:id>', methods = ['DELETE'])
def delete_course(id):
    # verify JWT and make sure that role is admin. 
    # Reworking my previous admin sorting to be more efficient. 
    if request.method == 'DELETE':
        payload = verify_jwt(request)
        sub = payload["sub"]
        query = client.query(kind=USERS)
        query.add_filter('sub', '=', sub)
        results = list(query.fetch())
        if len(results) == 0:
            return {"Error": "Unauthorized"}, 401
        else:
            # Get the course
            course_key = client.key(COURSES, id)
            course = client.get(key=course_key)
            if course is None:
                return {"Error": "You don't have permission on this resource"}, 403
            else:
                user = results[0]
                if user["role"] != "admin":
                    return {"Error": "You don't have permission on this resource"}, 403
                else:
                    # First delete the enrollment entries
                    query = client.query(kind=ENROLLMENT)
                    query.add_filter('course_id', '=', id)
                    results = list(query.fetch())
                    
                    for enrollment in results:
                        enrollment_key = client.key(ENROLLMENT, enrollment.key.id)
                        client.delete(enrollment_key)


                    # Second delete the course
                    client.delete(course_key)

                    return ('', 204)
    else:
        return jsonify(error = "Method not recognized")



# UPDATE enrollment in a course
# - PROTECTION: Only admin or JWT is owned by instructor of the course. 
# - I will use a single datastore entries called ENROLLMENT [id, course_id, student_id] to represent
@app.route('/' + COURSES + '/<int:id>' + '/' + STUDENTS, methods = ['PATCH'])
def update_enrollment(id):
    if request.method == 'PATCH':
        # Verify JWT first
        payload = verify_jwt(request)
        sub = payload["sub"]
        query = client.query(kind=USERS)
        query.add_filter('sub', '=', sub)
        results = list(query.fetch())
        if len(results) == 0:
            return {"Error": "Unauthorized"}, 401
        else:
            # Get the course
            course_key = client.key(COURSES, id)
            course = client.get(key=course_key)
            if course is None:
                return {"Error": "You don't have permission on this resource"}, 403
            else:
                # Verify admin or JWT instructor
                user = results[0]
                course_key = client.key(COURSES, id)
                course = client.get(key=course_key)
                instructor_id = course["instructor_id"]

                # Check if first admin, and if not check if JWT belongs to instructor of course. 
                if user["role"] != "admin":
                    if instructor_id != user.key.id:
                        return {"Error": "You don't have permission on this resource"}, 403
                
                # Check the body. 
                content = request.get_json()
                if len(content["add"]) != 0:
                    for student_id in content["add"]:
                        user_key = client.key(USERS, student_id)
                        user = client.get(key=user_key)
                        if user is None:
                            return {"Error": "Enrollment data is invalid"}, 409
                        if user["role"] != "student":
                            return {"Error": "Enrollment data is invalid"}, 409
                        
                        # Also check for common values in content["remove"]
                        if student_id in content["remove"]:
                            return {"Error": "Enrollment data is invalid"}, 409

                
                if len(content["remove"]) != 0:
                    for student_id in content["remove"]:
                        user_key = client.key(USERS, student_id)
                        user = client.get(key=user_key)
                        if user is None:
                            return {"Error": "Enrollment data is invalid"}, 409
                        if user["role"] != "student":
                            return {"Error": "Enrollment data is invalid"}, 409
                        
                        # Also check for common values in content["add"]
                        if student_id in content["add"]:
                            return {"Error": "Enrollment data is invalid"}, 409

                
                # Enrollment has been validated. 
                if len(content["add"]) != 0:
                    for student_id in content["add"]:
                        query = client.query(kind=ENROLLMENT)
                        query.add_filter('student_id', '=', student_id)
                        query.add_filter('course_id', '=', id)
                        results = list(query.fetch())
                        if len(results) != 0:
                            continue
                        else:
                            new_enrollment = datastore.Entity(key = client.key(ENROLLMENT))
                            new_enrollment.update({
                                "student_id": student_id,
                                "course_id": id
                            })
                            client.put(new_enrollment)
                
                if len(content["remove"]) != 0:
                    for student_id in content["remove"]:
                        query = client.query(kind=ENROLLMENT)
                        query.add_filter('student_id', '=', student_id)
                        query.add_filter('course_id', '=', id)
                        results = list(query.fetch())
                        if len(results) != 0:
                            enrollment = results[0]
                            enrollment_key = client.key(ENROLLMENT, enrollment.key.id)
                            client.delete(enrollment_key)
                        else:
                            continue
                return ('', 200)

    else:
        return jsonify(error = "Method not recognized")
    

# Get enrollment for a course
# PROTECTION: admin or when JWT is owned by instructor of the course
@app.route('/' + COURSES + '/<int:id>' + '/' + STUDENTS, methods=['GET'])
def get_enrollment(id):
    if request.method == 'GET':
        # Verify JWT first
        payload = verify_jwt(request)
        sub = payload["sub"]
        query = client.query(kind=USERS)
        query.add_filter('sub', '=', sub)
        results = list(query.fetch())
        if len(results) == 0:
            return {"Error": "Unauthorized"}, 401
        else:
            # Get the course
            course_key = client.key(COURSES, id)
            course = client.get(key=course_key)
            if course is None:
                return {"Error": "You don't have permission on this resource"}, 403
            else:
                # Verify admin or JWT instructor
                user = results[0]
                course_key = client.key(COURSES, id)
                course = client.get(key=course_key)
                instructor_id = course["instructor_id"]

                # Check if first admin, and if not check if JWT belongs to instructor of course. 
                if user["role"] != "admin":
                    if instructor_id != user.key.id:
                        return {"Error": "You don't have permission on this resource"}, 403
                
                # Get enrollment
                query = client.query(kind=ENROLLMENT)
                query.add_filter('course_id', '=', id)
                results = list(query.fetch())
                response = []
                for enrollment in results:
                    response.append(enrollment["student_id"])
                return response

                




if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
