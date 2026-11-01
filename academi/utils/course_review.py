"""Keep teacher changes to approved courses in the moderation queue."""


def require_course_review(course, user):
    if user.role != 'admin' and course.status == 'published':
        course.status = 'pending'
        course.rejection_reason = ''
        course.save(update_fields=['status', 'rejection_reason'])
