from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Review, Booking, User
from app.services.email_service import EmailService
from datetime import datetime
import logging

review_bp = Blueprint('review', __name__, url_prefix='/review')

@review_bp.route('/new/<int:booking_id>')
def new_review(booking_id):
    """Display review form for a completed booking"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if booking is completed
    if booking.status != 'completed':
        flash('Reviews can only be submitted for completed bookings.', 'warning')
        return redirect(url_for('main.index'))
    
    # Check if review already exists
    existing_review = Review.query.filter_by(booking_id=booking_id).first()
    if existing_review:
        flash('A review has already been submitted for this booking.', 'info')
        return render_template('review/view_review.html', review=existing_review)
    
    return render_template('review/new_review.html', booking=booking)

@review_bp.route('/submit', methods=['POST'])
def submit_review():
    """Submit a new customer review"""
    try:
        # Get form data
        booking_id = request.form.get('booking_id', type=int)
        rating = request.form.get('rating', type=int)
        title = request.form.get('title', '').strip()
        review_text = request.form.get('review_text', '').strip()
        
        # Optional detailed ratings
        technician_rating = request.form.get('technician_rating', type=int)
        timeliness_rating = request.form.get('timeliness_rating', type=int)
        communication_rating = request.form.get('communication_rating', type=int)
        value_rating = request.form.get('value_rating', type=int)
        
        # Optional feedback
        would_recommend = request.form.get('would_recommend') == 'on'
        is_public = request.form.get('is_public') == 'on'
        service_issues = request.form.get('service_issues', '').strip()
        suggestions = request.form.get('suggestions', '').strip()
        
        # Validate required fields
        if not booking_id or not rating:
            flash('Booking ID and rating are required.', 'danger')
            return redirect(request.referrer or url_for('main.index'))
        
        if rating < 1 or rating > 5:
            flash('Rating must be between 1 and 5 stars.', 'danger')
            return redirect(request.referrer or url_for('main.index'))
        
        # Get booking and validate
        booking = Booking.query.get_or_404(booking_id)
        
        if booking.status != 'completed':
            flash('Reviews can only be submitted for completed bookings.', 'warning')
            return redirect(url_for('main.index'))
        
        # Check if review already exists
        existing_review = Review.query.filter_by(booking_id=booking_id).first()
        if existing_review:
            flash('A review has already been submitted for this booking.', 'info')
            return redirect(url_for('review.view_review', review_id=existing_review.id))
        
        # Get customer info
        customer = booking.customer or booking.user
        
        # Get service information from booking
        device_type = booking.device_model
        if booking.booking_services:
            service_types = [bs.service.name for bs in booking.booking_services if bs.service]
            service_type = ', '.join(service_types) if service_types else 'Mobile Repair Service'
        else:
            service_type = 'Mobile Repair Service'
        
        # Create review
        review = Review(
            booking_id=booking_id,
            user_id=customer.id,
            rating=rating,
            title=title,
            review_text=review_text,
            technician_rating=technician_rating,
            timeliness_rating=timeliness_rating,
            communication_rating=communication_rating,
            value_rating=value_rating,
            would_recommend=would_recommend,
            is_public=is_public,
            service_issues=service_issues,
            suggestions=suggestions,
            device_type=device_type,
            service_type=service_type,
            is_verified=True  # Auto-verify since it's from a real booking
        )
        
        db.session.add(review)
        db.session.commit()
        
        # Send thank you email
        try:
            EmailService.send_review_thank_you(review)
        except Exception as e:
            current_app.logger.error(f"Failed to send review thank you email: {str(e)}")
        
        # Send admin notification
        try:
            EmailService.send_admin_notification(booking, 'review_submitted')
        except Exception as e:
            current_app.logger.error(f"Failed to send admin review notification: {str(e)}")
        
        flash('Thank you for your review! Your feedback is valuable to us.', 'success')
        return redirect(url_for('review.view_review', review_id=review.id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error submitting review: {str(e)}")
        flash('An error occurred while submitting your review. Please try again.', 'danger')
        return redirect(request.referrer or url_for('main.index'))

@review_bp.route('/view/<int:review_id>')
def view_review(review_id):
    """View a specific review"""
    review = Review.query.get_or_404(review_id)
    return render_template('review/view_review.html', review=review)

@review_bp.route('/all')
def all_reviews():
    """Display all public reviews"""
    page = request.args.get('page', 1, type=int)
    rating_filter = request.args.get('rating', type=int)
    
    # Get public reviews
    query = Review.query.filter_by(is_public=True, status='active', is_verified=True)
    
    if rating_filter:
        query = query.filter(Review.rating >= rating_filter)
    
    reviews = query.order_by(Review.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # Get rating statistics
    average_rating = Review.get_average_rating()
    rating_distribution = Review.get_rating_distribution()
    total_reviews = Review.query.filter_by(status='active', is_verified=True).count()
    
    return render_template('review/all_reviews.html', 
                         reviews=reviews,
                         average_rating=average_rating,
                         rating_distribution=rating_distribution,
                         total_reviews=total_reviews,
                         current_rating_filter=rating_filter)

@review_bp.route('/api/submit', methods=['POST'])
def api_submit_review():
    """API endpoint for submitting reviews"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'booking_id' not in data or 'rating' not in data:
            return jsonify({'error': 'Booking ID and rating are required'}), 400
        
        booking_id = data['booking_id']
        rating = data['rating']
        
        if rating < 1 or rating > 5:
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        # Get booking and validate
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        if booking.status != 'completed':
            return jsonify({'error': 'Reviews can only be submitted for completed bookings'}), 400
        
        # Check if review already exists
        existing_review = Review.query.filter_by(booking_id=booking_id).first()
        if existing_review:
            return jsonify({'error': 'Review already exists for this booking'}), 400
        
        # Get customer info
        customer = booking.customer or booking.user
        
        # Create review with provided data
        review = Review(
            booking_id=booking_id,
            user_id=customer.id,
            rating=rating,
            title=data.get('title', ''),
            review_text=data.get('review_text', ''),
            technician_rating=data.get('technician_rating'),
            timeliness_rating=data.get('timeliness_rating'),
            communication_rating=data.get('communication_rating'),
            value_rating=data.get('value_rating'),
            would_recommend=data.get('would_recommend', True),
            is_public=data.get('is_public', True),
            service_issues=data.get('service_issues', ''),
            suggestions=data.get('suggestions', ''),
            device_type=booking.device_model,
            service_type=', '.join([bs.service.name for bs in booking.booking_services if bs.service]) or 'Mobile Repair Service',
            is_verified=True
        )
        
        db.session.add(review)
        db.session.commit()
        
        # Send notifications (background task in production)
        try:
            EmailService.send_review_thank_you(review)
            EmailService.send_admin_notification(booking, 'review_submitted')
        except Exception as e:
            current_app.logger.error(f"Failed to send review notifications: {str(e)}")
        
        return jsonify({
            'message': 'Review submitted successfully',
            'review_id': review.id,
            'review': review.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"API Error submitting review: {str(e)}")
        return jsonify({'error': 'An error occurred while submitting the review'}), 500

@review_bp.route('/api/stats')
def api_review_stats():
    """API endpoint for review statistics"""
    try:
        average_rating = Review.get_average_rating()
        rating_distribution = Review.get_rating_distribution()
        total_reviews = Review.query.filter_by(status='active', is_verified=True).count()
        recent_reviews = Review.get_recent_reviews(days=30, limit=5)
        
        return jsonify({
            'average_rating': average_rating,
            'rating_distribution': rating_distribution,
            'total_reviews': total_reviews,
            'recent_reviews': [review.to_dict() for review in recent_reviews]
        })
        
    except Exception as e:
        current_app.logger.error(f"API Error getting review stats: {str(e)}")
        return jsonify({'error': 'An error occurred while getting review statistics'}), 500

# Admin routes for review management
@review_bp.route('/admin/respond/<int:review_id>', methods=['POST'])
@login_required
def admin_respond(review_id):
    """Admin response to a review"""
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    review = Review.query.get_or_404(review_id)
    admin_response = request.form.get('admin_response', '').strip()
    
    if admin_response:
        review.admin_response = admin_response
        review.admin_response_by = current_user.id
        review.admin_response_at = datetime.utcnow()
        
        db.session.commit()
        flash('Response added successfully.', 'success')
    else:
        flash('Response cannot be empty.', 'warning')
    
    return redirect(url_for('admin.reviews'))

@review_bp.route('/admin/moderate/<int:review_id>', methods=['POST'])
@login_required
def admin_moderate(review_id):
    """Admin moderation of reviews"""
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    review = Review.query.get_or_404(review_id)
    action = request.form.get('action')
    reason = request.form.get('reason', '').strip()
    
    if action == 'hide':
        review.status = 'hidden'
        review.flagged_reason = reason
        review.moderated_by = current_user.id
        review.moderated_at = datetime.utcnow()
        flash('Review hidden successfully.', 'success')
    elif action == 'flag':
        review.status = 'flagged'
        review.flagged_reason = reason
        review.moderated_by = current_user.id
        review.moderated_at = datetime.utcnow()
        flash('Review flagged successfully.', 'warning')
    elif action == 'activate':
        review.status = 'active'
        review.flagged_reason = None
        review.moderated_by = current_user.id
        review.moderated_at = datetime.utcnow()
        flash('Review activated successfully.', 'success')
    
    db.session.commit()
    return redirect(url_for('admin.reviews')) 