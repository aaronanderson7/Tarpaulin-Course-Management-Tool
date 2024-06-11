# Tarpaulin-Course-Management-Tool

- Name: Aaron Anderson
- Date: 06/10/2024
- Summary: Google Cloud RESTful API
- Name: Tarpaulin Course Management Tool


# Introduction

The application for which you’ll write a REST API for this project is Tarpaulin, a lightweight course management tool. The Tarpaulin REST API has 13 endpoints, most of which are protected. The protected endpoints require a valid JWT in the request as Bearer token in the Authorization header. Each user in Tarpaulin has one of three roles: admin, instructor, and student.

# Endpoints

Here is a summary of the endpoints you need to implement (the link to the full API spec is provided in the next section)


1. User login

```POST /users/login```

- Pre-created Auth0 users with username and password

- Use Auth0 to issue JWTs. Feel free to  use the code of the example app presented in Exploration - Implementing Auth Using JWTs. Requires only a minor changes in the response.

2. Get all users

```GET /users```

- Protection: Admin only

Summary information of all 9 users. No info about avatar or courses.

3. Get a user

```GET /users/:id```

- Protection: Admin. Or user with JWT matching id

- Detailed info about the user, including avatar (if any) and courses (for instructors and students)

4. Create/update a user’s avatar

```POST /users/:id/avatar```

- Protection: User with JWT matching id

- Upload file to Google Cloud Storage.

5. Get a user’s avatar

```GET /users/:id/avatar```

- Protection: User with JWT matching id

- Read and return file from Google Cloud Storage.

6. Delete a user’s avatar

```DELETE /users/:id/avatar```

- Protection: User with JWT matching id

- Delete file from Google Cloud Storage.

7. Create a course

```POST /courses```

- Protection: Admin only

- Create a course.

8. Get all courses

```GET /courses```

- Protection: Unprotected

- Paginated using offset/limit. Page size is 3. Ordered by “subject.”  Doesn’t return info on course enrollment.

9. Get a course

```GET /course/:id```

- Protection: Unprotected

- Doesn’t return info on course enrollment.

10. Update a course

```PATCH /course/:id```

- Protection: Admin only

- Partial update.

11. Delete a course

```DELETE /course/:id```

- Protection: Admin only

- Delete course and delete enrollment info about the course.

12. Update enrollment in a course

```PATCH /courses/:id/students```

- Protection: Admin. Or instructor of the course.

- Enroll or disenroll students from the course.

13. Get enrollment for a course

```GET /courses/:id/students```

- Protection: Admin. Or instructor of the course.

- All students enrolled in the course.


# Data

Using Google Cloud Datastore to build Entities for the Tarpaulin Course Management Tool. 

1. Users
- Description: users entity represents the users of the Tarpaulin Course Management Tool.

<img width="550" alt="Screen Shot 2024-06-11 at 9 37 00 AM" src="https://github.com/aaronanderson7/Tarpaulin-Course-Management-Tool/assets/107898465/8a228b6a-28f2-43a5-8070-3f0b787361c2">

2. Courses
- Description: courses entity represents a unique course in the Tarpaulin course management tool.

<img width="548" alt="Screen Shot 2024-06-11 at 9 37 42 AM" src="https://github.com/aaronanderson7/Tarpaulin-Course-Management-Tool/assets/107898465/041f8962-5639-4f1a-9170-9d873b36b9c3">

3. Avatar
- Description: avatar entity represents the possible avatar image of the user. The property “avatar” is the name of the image stored in Google Cloud Bucket.

<img width="548" alt="Screen Shot 2024-06-11 at 9 38 19 AM" src="https://github.com/aaronanderson7/Tarpaulin-Course-Management-Tool/assets/107898465/913474ec-9681-40df-a18f-a4a634b590dd">

4. Enrollment
- Description: enrollment entity represents a singular student enrolled in a singular course for the Tarpaulin Course Management tool.

<img width="542" alt="Screen Shot 2024-06-11 at 9 38 30 AM" src="https://github.com/aaronanderson7/Tarpaulin-Course-Management-Tool/assets/107898465/3674d994-35db-4508-9d62-caade2737c1f">

# Testing

Used a postman collection and environment to test the RESTful API. 



 
