#!/usr/bin/python3
"""reviews module to handle reviews routes"""
from api.v1.views import app_views
from models import storage
from flask import jsonify, abort, request
from models.review import Review


@app_views.route('/reviews', methods=['GET'], strict_slashes=False)
def reviews():
    """retrieve all reviews"""
    all_reviews = storage.all(Review).values()

    return jsonify([review.to_dict() for review in all_reviews])

@app_views.route('/reviews/<review_id>', methods=['GET'], strict_slashes=False)
def get_review(review_id):
    """retrieve one review using id"""
    review = storage.get(Review, review_id)
    if not review:
        abort(404)

    return jsonify(review.to_dict())

@app_views.route('/reviews/<review_id>', methods=['DELETE'], strict_slashes=False)
def delete_review(review_id):
    """delete a review using id"""
    review = storage.get(Review, review_id)
    if not review:
        abort(404)

    storage.delete(review)
    storage.save()
    return jsonify({}),200

@app_views.route('/reviews', methods=['POST'], strict_slashes=False)
def create_review():
    """create new review"""
    data = request.get_json(silent=True)

    if data is None:
        abort(400, description="Not a JSON")

    if "text" not in data:
        abort(400, "Missing text")

    review = Review(text=data["text"])
    review.save()

    return jsonify(review.to_dict()), 201

@app_views.route('/reviews/<review_id>', methods=['PUT'], strict_slashes=False)
def update_review(review_id):
    """update a review using id"""
    review = storage.get(Review, review_id)
    if not review:
        abort(404)

    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="Not a JSON")

    for key, value in data.items():
        if key not in ['id', 'created_at', 'updated_at']:
            setattr(review, key, value)

    storage.save()
    return jsonify(review.to_dict()), 200
