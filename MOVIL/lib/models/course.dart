import '../core/utils/json_utils.dart';

class CategoryItem {
  CategoryItem({required this.id, required this.name, this.description = '', this.coursesCount = 0});

  final int id;
  final String name, description;
  final int coursesCount;

  factory CategoryItem.fromJson(Map<String, dynamic> j) => CategoryItem(
        id: asInt(j['id']),
        name: asString(j['name']),
        description: asString(j['description']),
        coursesCount: asInt(j['courses_count']),
      );
}

class CouponInfo {
  CouponInfo({required this.code, required this.type, required this.value, this.expiresAt});

  final String code, type;
  final double value;
  final DateTime? expiresAt;

  String get label => type == 'percentage' ? '-${value.toStringAsFixed(0)}%' : '-Bs. ${value.toStringAsFixed(0)}';

  factory CouponInfo.fromJson(Map<String, dynamic> j) => CouponInfo(
        code: asString(j['code']),
        type: asString(j['type']),
        value: asDouble(j['value']),
        expiresAt: asDate(j['expires_at']),
      );
}

class LessonOutline {
  LessonOutline({
    required this.id,
    required this.title,
    required this.type,
    this.durationMinutes = 0,
    this.isFree = false,
    this.completed = false,
  });

  final int id;
  final String title, type;
  final int durationMinutes;
  final bool isFree, completed;

  factory LessonOutline.fromJson(Map<String, dynamic> j) => LessonOutline(
        id: asInt(j['id']),
        title: asString(j['title']),
        type: asString(j['type']),
        durationMinutes: asInt(j['duration_minutes']),
        isFree: asBool(j['is_free']),
        completed: asBool(j['completed']),
      );
}

class ModuleOutline {
  ModuleOutline({required this.id, required this.title, this.description = '', required this.lessons});

  final int id;
  final String title, description;
  final List<LessonOutline> lessons;

  factory ModuleOutline.fromJson(Map<String, dynamic> j) => ModuleOutline(
        id: asInt(j['id']),
        title: asString(j['title']),
        description: asString(j['description']),
        lessons: asList(j['lessons']).map(LessonOutline.fromJson).toList(),
      );
}

class Review {
  Review({
    required this.id,
    required this.student,
    required this.rating,
    this.comment = '',
    this.isEdited = false,
    this.picture,
    this.createdAt,
    this.course,
  });

  final int id, rating;
  final String student, comment;
  final bool isEdited;
  final String? picture, course;
  final DateTime? createdAt;

  factory Review.fromJson(Map<String, dynamic> j) => Review(
        id: asInt(j['id']),
        student: asString(j['student']),
        rating: asInt(j['rating']),
        comment: asString(j['comment']),
        isEdited: asBool(j['is_edited']),
        picture: asStringOrNull(j['picture']),
        createdAt: asDate(j['created_at']),
        course: asStringOrNull(j['course']),
      );
}

class TeacherInfo {
  TeacherInfo({
    required this.id,
    required this.name,
    this.specialty = '',
    this.institution = '',
    this.bio = '',
    this.experienceYears = '',
    this.linkedin = '',
    this.website = '',
    this.picture,
    this.coursesCount = 0,
    this.studentsCount = 0,
    this.rating = 0,
  });

  final int id, coursesCount, studentsCount;
  final String name, specialty, institution, bio, experienceYears, linkedin, website;
  final String? picture;
  final double rating;

  factory TeacherInfo.fromJson(Map<String, dynamic> j) => TeacherInfo(
        id: asInt(j['id']),
        name: asString(j['name']),
        specialty: asString(j['specialty']),
        institution: asString(j['institution']),
        bio: asString(j['bio']),
        experienceYears: asString(j['experience_years']),
        linkedin: asString(j['linkedin']),
        website: asString(j['website']),
        picture: asStringOrNull(j['picture']),
        coursesCount: asInt(j['courses_count']),
        studentsCount: asInt(j['students_count']),
        rating: asDouble(j['rating']),
      );
}

/// Curso: sirve tanto para las tarjetas del catálogo como para el detalle
/// (los campos del detalle vienen vacíos en las tarjetas).
class Course {
  Course({
    required this.id,
    required this.title,
    required this.description,
    this.image,
    this.category,
    this.categoryId,
    required this.level,
    required this.levelLabel,
    required this.price,
    required this.isFree,
    required this.priceLabel,
    required this.isFeatured,
    required this.teacher,
    required this.rating,
    required this.reviewsCount,
    required this.studentsCount,
    required this.lessonsCount,
    required this.durationMinutes,
    required this.isEnrolled,
    required this.isFavorite,
    this.coupon,
    this.status,
    this.statusLabel,
    this.rejectionReason,
    // detalle
    this.videoPromo,
    this.modules = const [],
    this.reviews = const [],
    this.userReview,
    this.teacherInfo,
    this.teacherCourses = const [],
    this.ratingDistribution = const {},
    this.progress,
    this.inCart = false,
    this.emiDiscount,
  });

  final int id, reviewsCount, studentsCount, lessonsCount, durationMinutes;
  final int? categoryId;
  final String title, description, level, levelLabel, priceLabel, teacher;
  final String? image, category, status, statusLabel, rejectionReason, videoPromo;
  final double price, rating;
  final bool isFree, isFeatured, isEnrolled, isFavorite, inCart;
  final CouponInfo? coupon;
  final List<ModuleOutline> modules;
  final List<Review> reviews;
  final Review? userReview;
  final TeacherInfo? teacherInfo;
  final List<Course> teacherCourses;
  final Map<int, int> ratingDistribution;
  final int? progress;
  final double? emiDiscount;

  Course copyWith({bool? isFavorite, bool? inCart}) => Course(
        id: id,
        title: title,
        description: description,
        image: image,
        category: category,
        categoryId: categoryId,
        level: level,
        levelLabel: levelLabel,
        price: price,
        isFree: isFree,
        priceLabel: priceLabel,
        isFeatured: isFeatured,
        teacher: teacher,
        rating: rating,
        reviewsCount: reviewsCount,
        studentsCount: studentsCount,
        lessonsCount: lessonsCount,
        durationMinutes: durationMinutes,
        isEnrolled: isEnrolled,
        isFavorite: isFavorite ?? this.isFavorite,
        coupon: coupon,
        status: status,
        statusLabel: statusLabel,
        rejectionReason: rejectionReason,
        videoPromo: videoPromo,
        modules: modules,
        reviews: reviews,
        userReview: userReview,
        teacherInfo: teacherInfo,
        teacherCourses: teacherCourses,
        ratingDistribution: ratingDistribution,
        progress: progress,
        inCart: inCart ?? this.inCart,
        emiDiscount: emiDiscount,
      );

  factory Course.fromJson(Map<String, dynamic> j) {
    final dist = <int, int>{};
    final rawDist = j['rating_distribution'];
    if (rawDist is Map) {
      rawDist.forEach((k, v) => dist[asInt(k)] = asInt(v));
    }
    return Course(
      id: asInt(j['id']),
      title: asString(j['title']),
      description: asString(j['description']),
      image: asStringOrNull(j['image']),
      category: asStringOrNull(j['category']),
      categoryId: j['category_id'] == null ? null : asInt(j['category_id']),
      level: asString(j['level'], 'beginner'),
      levelLabel: asString(j['level_label']),
      price: asDouble(j['price']),
      isFree: asBool(j['is_free']),
      priceLabel: asString(j['price_label']),
      isFeatured: asBool(j['is_featured']),
      teacher: asString(j['teacher']),
      rating: asDouble(j['rating']),
      reviewsCount: asInt(j['reviews_count']),
      studentsCount: asInt(j['students_count']),
      lessonsCount: asInt(j['lessons_count']),
      durationMinutes: asInt(j['duration_minutes']),
      isEnrolled: asBool(j['is_enrolled']),
      isFavorite: asBool(j['is_favorite']),
      coupon: j['coupon'] is Map<String, dynamic> ? CouponInfo.fromJson(j['coupon']) : null,
      status: asStringOrNull(j['status']),
      statusLabel: asStringOrNull(j['status_label']),
      rejectionReason: asStringOrNull(j['rejection_reason']),
      videoPromo: asStringOrNull(j['video_promo']),
      modules: asList(j['modules']).map(ModuleOutline.fromJson).toList(),
      reviews: asList(j['reviews']).map(Review.fromJson).toList(),
      userReview: j['user_review'] is Map<String, dynamic> ? Review.fromJson(j['user_review']) : null,
      teacherInfo: j['teacher_info'] is Map<String, dynamic> ? TeacherInfo.fromJson(j['teacher_info']) : null,
      teacherCourses: asList(j['teacher_courses']).map(Course.fromJson).toList(),
      ratingDistribution: dist,
      progress: j['progress'] == null ? null : asInt(j['progress']),
      inCart: asBool(j['in_cart']),
      emiDiscount: j['emi_discount'] == null ? null : asDouble(j['emi_discount']),
    );
  }
}
