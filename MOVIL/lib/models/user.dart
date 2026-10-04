import '../core/utils/json_utils.dart';

class AppUser {
  AppUser({
    required this.id,
    required this.username,
    required this.email,
    required this.role,
    required this.name,
    required this.emailVerified,
    this.phone = '',
    this.bio = '',
    this.city = '',
    this.university = '',
    this.career = '',
    this.semester = '',
    this.educationLevel = '',
    this.interests = '',
    this.specialty = '',
    this.institution = '',
    this.experienceYears = '',
    this.teacherBio = '',
    this.linkedin = '',
    this.website = '',
    this.picture,
  });

  final int id;
  final String username, email, role, name;
  final bool emailVerified;
  final String phone, bio, city, university, career, semester, educationLevel, interests;
  final String specialty, institution, experienceYears, teacherBio, linkedin, website;
  final String? picture;

  bool get isStudent => role == 'student';
  bool get isTeacher => role == 'teacher';
  bool get isAdmin => role == 'admin';

  String get roleLabel => switch (role) {
        'teacher' => 'Docente',
        'admin' => 'Administrador',
        _ => 'Estudiante',
      };

  factory AppUser.fromJson(Map<String, dynamic> j) => AppUser(
        id: asInt(j['id']),
        username: asString(j['username']),
        email: asString(j['email']),
        role: asString(j['role'], 'student'),
        name: asString(j['name']),
        emailVerified: asBool(j['email_verified']),
        phone: asString(j['phone']),
        bio: asString(j['bio']),
        city: asString(j['city']),
        university: asString(j['university']),
        career: asString(j['career']),
        semester: asString(j['semester']),
        educationLevel: asString(j['education_level']),
        interests: asString(j['interests']),
        specialty: asString(j['specialty']),
        institution: asString(j['institution']),
        experienceYears: asString(j['experience_years']),
        teacherBio: asString(j['teacher_bio']),
        linkedin: asString(j['linkedin']),
        website: asString(j['website']),
        picture: asStringOrNull(j['picture']),
      );
}
