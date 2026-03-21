#!/usr/bin/python3
"""Integration tests for the REST API."""
import json
import os
import unittest
from hashlib import md5

from api.v1.app import app
from models import storage, storage_t
from models.amenity import Amenity
from models.city import City
from models.place import Place
from models.review import Review
from models.state import State
from models.user import User


class APITestCase(unittest.TestCase):
    """Base helpers for API integration tests."""

    def setUp(self):
        """Create a test client and isolate storage state when possible."""
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.created_objects = []
        self.file_backup = None
        self.objects_backup = None
        if storage_t != "db":
            self._backup_file_storage()

    def tearDown(self):
        """Clean up created objects and restore file storage state."""
        if storage_t == "db":
            self._cleanup_db_objects()
        else:
            self._restore_file_storage()

    def _backup_file_storage(self):
        """Back up the file storage dictionary and JSON file."""
        self.objects_backup = storage._FileStorage__objects.copy()
        if os.path.exists("file.json"):
            with open("file.json", "r") as file_obj:
                self.file_backup = file_obj.read()
        storage._FileStorage__objects = {}
        storage.save()

    def _restore_file_storage(self):
        """Restore the original file storage dictionary and JSON file."""
        storage._FileStorage__objects = self.objects_backup
        if self.file_backup is None:
            if os.path.exists("file.json"):
                os.remove("file.json")
        else:
            with open("file.json", "w") as file_obj:
                file_obj.write(self.file_backup)

    def _cleanup_db_objects(self):
        """Delete objects created during a DB-backed test."""
        for obj in reversed(self.created_objects):
            current = storage.get(obj.__class__, obj.id)
            if current is not None:
                storage.delete(current)
        if self.created_objects:
            storage.save()
        storage.close()
        storage.reload()

    def create_state(self, name="Cairo"):
        """Create and persist a state for test setup."""
        state = State(name=name)
        state.save()
        self.created_objects.append(state)
        return state

    def create_city(self, state, name="Nasr City"):
        """Create and persist a city for test setup."""
        city = City(name=name, state_id=state.id)
        city.save()
        self.created_objects.append(city)
        return city

    def create_user(self, email="user@example.com", password="secret"):
        """Create and persist a user for test setup."""
        user = User(email=email, password=password)
        user.save()
        self.created_objects.append(user)
        return user

    def create_place(self, user, city, name="Sunny flat"):
        """Create and persist a place for test setup."""
        place = Place(
            name=name,
            user_id=user.id,
            city_id=city.id,
            description="nice stay"
        )
        place.save()
        self.created_objects.append(place)
        return place

    def create_review(self, user, place, text="Great stay"):
        """Create and persist a review for test setup."""
        review = Review(text=text, user_id=user.id, place_id=place.id)
        review.save()
        self.created_objects.append(review)
        return review

    def create_amenity(self, name="WiFi"):
        """Create and persist an amenity for test setup."""
        amenity = Amenity(name=name)
        amenity.save()
        self.created_objects.append(amenity)
        return amenity


class TestIndexRoutes(APITestCase):
    """Tests for status and stats routes."""

    def test_status_route(self):
        """`/status` returns an OK payload."""
        response = self.client.get("/api/v1/status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "Ok"})

    def test_stats_route_reflects_created_objects(self):
        """`/stats` counts objects across resources."""
        before = self.client.get("/api/v1/stats").get_json()
        self.create_state()
        self.create_user()
        self.create_amenity()
        after = self.client.get("/api/v1/stats").get_json()

        self.assertEqual(after["states"], before["states"] + 1)
        self.assertEqual(after["users"], before["users"] + 1)
        self.assertEqual(after["amenities"], before["amenities"] + 1)

    def test_cors_header_is_set_for_matching_origin(self):
        """Responses include the configured CORS header."""
        response = self.client.get(
            "/api/v1/status",
            headers={"Origin": "0.0.0.0"}
        )
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"),
                         "0.0.0.0")

    def test_unknown_route_returns_json_404(self):
        """Unknown routes return the API 404 payload."""
        response = self.client.get("/api/v1/does-not-exist")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"error": "Not found"})


class TestUserRoutes(APITestCase):
    """Tests for user routes."""

    def test_create_user_hashes_password_and_hides_it(self):
        """POST `/users` hashes the password and omits it from JSON."""
        response = self.client.post(
            "/api/v1/users",
            json={"email": "me@example.com", "password": "secret"}
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertNotIn("password", payload)
        self.assertEqual(payload["email"], "me@example.com")

        saved_user = storage.get(User, payload["id"])
        self.created_objects.append(saved_user)
        self.assertEqual(saved_user.password,
                         md5("secret".encode("utf-8")).hexdigest())

    def test_create_user_rejects_missing_fields(self):
        """POST `/users` validates required fields."""
        missing_email = self.client.post(
            "/api/v1/users",
            json={"password": "secret"}
        )
        missing_password = self.client.post(
            "/api/v1/users",
            json={"email": "me@example.com"}
        )

        self.assertEqual(missing_email.status_code, 400)
        self.assertIn("Missing email", missing_email.get_data(as_text=True))
        self.assertEqual(missing_password.status_code, 400)
        self.assertIn("Missing password",
                      missing_password.get_data(as_text=True))

    def test_update_user_ignores_protected_fields(self):
        """PUT `/users/<id>` ignores protected attributes."""
        user = self.create_user()
        original_email = user.email
        response = self.client.put(
            "/api/v1/users/{}".format(user.id),
            json={
                "email": "changed@example.com",
                "first_name": "Alaa",
                "password": "newpass"
            }
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["email"], original_email)
        self.assertEqual(payload["first_name"], "Alaa")
        self.assertNotIn("password", payload)

        stored_user = storage.get(User, user.id)
        self.assertEqual(stored_user.email, original_email)
        self.assertEqual(stored_user.first_name, "Alaa")
        self.assertEqual(stored_user.password,
                         md5("newpass".encode("utf-8")).hexdigest())

    def test_get_missing_user_returns_404(self):
        """GET `/users/<id>` returns 404 for unknown users."""
        response = self.client.get("/api/v1/users/missing-id")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"error": "Not found"})


class TestStateAndCityRoutes(APITestCase):
    """Tests for state and city routes."""

    def test_create_and_update_state(self):
        """State create and update routes work with JSON payloads."""
        create = self.client.post("/api/v1/states", json={"name": "Alex"})
        self.assertEqual(create.status_code, 201)
        state_id = create.get_json()["id"]
        self.created_objects.append(storage.get(State, state_id))

        update = self.client.put(
            "/api/v1/states/{}".format(state_id),
            json={"name": "Giza", "id": "ignored"}
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.get_json()["name"], "Giza")
        self.assertEqual(update.get_json()["id"], state_id)

    def test_create_state_rejects_invalid_payload(self):
        """State creation rejects non-JSON and missing names."""
        not_json = self.client.post(
            "/api/v1/states",
            data="name=Alex",
            content_type="text/plain"
        )
        missing_name = self.client.post("/api/v1/states", json={})

        self.assertEqual(not_json.status_code, 400)
        self.assertIn("Not a JSON", not_json.get_data(as_text=True))
        self.assertEqual(missing_name.status_code, 400)
        self.assertIn("Missing name", missing_name.get_data(as_text=True))

    def test_city_routes_support_nested_create_list_and_delete(self):
        """City routes support state nesting and CRUD behavior."""
        state = self.create_state()

        create = self.client.post(
            "/api/v1/states/{}/cities".format(state.id),
            json={"name": "Maadi"}
        )
        self.assertEqual(create.status_code, 201)
        city_id = create.get_json()["id"]
        self.created_objects.append(storage.get(City, city_id))

        listing = self.client.get("/api/v1/states/{}/cities".format(state.id))
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.get_json()), 1)

        delete = self.client.delete("/api/v1/cities/{}".format(city_id))
        self.assertEqual(delete.status_code, 200)
        self.assertEqual(delete.get_json(), {})

    def test_city_routes_handle_missing_resources(self):
        """City routes return 404 for unknown state or city IDs."""
        list_response = self.client.get("/api/v1/states/missing/cities")
        create_response = self.client.post(
            "/api/v1/states/missing/cities",
            json={"name": "Maadi"}
        )

        self.assertEqual(list_response.status_code, 404)
        self.assertEqual(create_response.status_code, 404)


class TestAmenityRoutes(APITestCase):
    """Tests for amenity routes."""

    def test_amenity_crud_flow(self):
        """Amenity endpoints support create, list, update, and delete."""
        create = self.client.post("/api/v1/amenities", json={"name": "Pool"})
        self.assertEqual(create.status_code, 201)
        amenity_id = create.get_json()["id"]
        self.created_objects.append(storage.get(Amenity, amenity_id))

        listing = self.client.get("/api/v1/amenities")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.get_json()), 1)

        update = self.client.put(
            "/api/v1/amenities/{}".format(amenity_id),
            json={"name": "Gym"}
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.get_json()["name"], "Gym")

        delete = self.client.delete("/api/v1/amenities/{}".format(amenity_id))
        self.assertEqual(delete.status_code, 200)
        self.assertEqual(delete.get_json(), {})

    def test_amenity_create_rejects_non_json_payload(self):
        """Amenity creation requires a JSON payload."""
        response = self.client.post(
            "/api/v1/amenities",
            data=json.dumps({"name": "Pool"}),
            content_type="text/plain"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Not a JSON", response.get_data(as_text=True))


class TestPlaceReviewAndAmenityRoutes(APITestCase):
    """Tests for place, review, and place-amenity routes."""

    def test_place_create_update_and_get(self):
        """Place endpoints support create, retrieve, and update."""
        create = self.client.post("/api/v1/places", json={"name": "Loft"})
        self.assertEqual(create.status_code, 201)
        place_id = create.get_json()["id"]
        self.created_objects.append(storage.get(Place, place_id))

        get_response = self.client.get("/api/v1/places/{}".format(place_id))
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.get_json()["name"], "Loft")

        update = self.client.put(
            "/api/v1/places/{}".format(place_id),
            json={"name": "Large Loft"}
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.get_json()["name"], "Large Loft")

    def test_review_create_update_and_delete(self):
        """Review endpoints support create, update, and delete."""
        create = self.client.post("/api/v1/reviews", json={"text": "Great"})
        self.assertEqual(create.status_code, 201)
        review_id = create.get_json()["id"]
        self.created_objects.append(storage.get(Review, review_id))

        update = self.client.put(
            "/api/v1/reviews/{}".format(review_id),
            json={"text": "Excellent"}
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.get_json()["text"], "Excellent")

        delete = self.client.delete("/api/v1/reviews/{}".format(review_id))
        self.assertEqual(delete.status_code, 200)
        self.assertEqual(delete.get_json(), {})

    def test_place_amenity_link_routes(self):
        """Place and amenity linking endpoints work end-to-end."""
        state = self.create_state()
        city = self.create_city(state)
        user = self.create_user()
        place = self.create_place(user, city)
        amenity = self.create_amenity()

        create_link = self.client.post(
            "/api/v1/places/{}/amenities/{}".format(place.id, amenity.id)
        )
        self.assertEqual(create_link.status_code, 201)
        self.assertEqual(create_link.get_json()["id"], amenity.id)

        duplicate_link = self.client.post(
            "/api/v1/places/{}/amenities/{}".format(place.id, amenity.id)
        )
        self.assertEqual(duplicate_link.status_code, 200)

        listing = self.client.get("/api/v1/places/{}/amenities".format(place.id))
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.get_json()), 1)

        delete_link = self.client.delete(
            "/api/v1/places/{}/amenities/{}".format(place.id, amenity.id)
        )
        self.assertEqual(delete_link.status_code, 200)
        self.assertEqual(delete_link.get_json(), {})

    def test_place_amenity_link_404s_for_missing_objects(self):
        """Place-amenity routes reject unknown IDs."""
        response = self.client.post("/api/v1/places/missing/amenities/missing")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"error": "Not found"})
