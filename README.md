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
 
