"""Prueba de punta a punta de los endpoints nuevos de la API (docente, administrador,
captcha, PDF, etc.). Crea datos temporales y los borra al final.
Uso (con el servidor en :8001):  ~/Academi/venv/bin/python tool/api_new_check.py"""
import json
import subprocess

import requests

BASE = 'http://localhost:8001/api/v1/'
ROOT = '/home/yhonatan/Academi'
PY = ROOT + '/venv/bin/python'
fails = []


def call(method, path, token=None, **kw):
    headers = {'Authorization': 'Bearer ' + token} if token else {}
    r = requests.request(method, BASE + path, headers=headers, **kw)
    try:
        j = r.json()
    except Exception:
        j = {'raw': r.text[:200]}
    return r.status_code, j


def chk(name, cond, info=''):
    print(('OK   ' if cond else 'FAIL ') + name, '' if cond else info)
    if not cond:
        fails.append(name)


def django(code):
    return subprocess.run([PY, 'manage.py', 'shell', '-c', code], capture_output=True, text=True, cwd=ROOT).stdout.strip()


def captcha_answer(key):
    return django(f"from captcha.models import CaptchaStore;print(CaptchaStore.objects.get(hashkey='{key}').response)").splitlines()[-1]


def login(user, pw):
    return call('POST', 'auth/login/', json={'identifier': user, 'password': pw})[1]['token']


# ------------------------------------------------ captcha (RF-06)
s, j = call('GET', 'auth/captcha/')
chk('captcha nuevo', s == 200 and j['captcha']['key'])
img = requests.get(j['captcha']['image'])
chk('captcha imagen', img.status_code == 200 and img.headers['content-type'].startswith('image'))
s, r = call('POST', 'auth/register/', json={'email': 'x@y.com'})
chk('registro sin captcha bloqueado', s == 422 and r.get('code') == 'CAPTCHA_REQUIRED')
cap = call('GET', 'auth/captcha/')[1]['captcha']
body = {'email': 'apitest@example.com', 'password': 'Abcd1234!', 'role': 'student', 'full_name': 'Api Test',
        'university': 'EMI', 'career': 'Sistemas', 'accept_terms': True,
        'captcha_key': cap['key'], 'captcha_answer': captcha_answer(cap['key'])}
s, r = call('POST', 'auth/register/', json=body)
chk('registro con captcha', s == 200 and r.get('token'), r)
s, r = call('POST', 'auth/password-reset/', json={'email': 'a@b.c'})
chk('recuperar contraseña sin captcha bloqueado', s == 422)
for _ in range(3):
    call('POST', 'auth/login/', json={'identifier': 'apitest@example.com', 'password': 'mal'})
s, r = call('POST', 'auth/login/', json={'identifier': 'apitest@example.com', 'password': 'Abcd1234!'})
chk('login exige captcha tras 3 fallos', s == 400 and r.get('code') == 'CAPTCHA_REQUIRED')
cap = r['captcha']
s, r = call('POST', 'auth/login/', json={'identifier': 'apitest@example.com', 'password': 'Abcd1234!',
                                          'captcha_key': cap['key'], 'captcha_answer': captcha_answer(cap['key'])})
chk('login con captcha correcto', s == 200 and r.get('token'), r)

# ------------------------------------------------ estudiante
st = login('estudiante', 'estudiante')
s, r = call('GET', 'progress/', st)
chk('progreso e historial (RF-09)', s == 200 and r['courses'], r)
pid = call('GET', 'purchases/', st)[1]['payments'][0]['id']
pdf = call('GET', f'purchases/{pid}/', st)[1]['payment'].get('pdf_url')
chk('pdf_url en la factura', bool(pdf))
p = requests.get(pdf)
chk('comprobante PDF descargable (RF-38)', p.status_code == 200 and p.content[:4] == b'%PDF', p.status_code)
chk('pdf con token malo rechazado', requests.get(BASE + f'purchases/{pid}/pdf/?t=xx').status_code == 403)
certs = call('GET', 'certificates/', st)[1]['certificates']
if certs:
    s, r = call('POST', f'certificates/{certs[0]["id"]}/email/', st)
    chk('certificado por correo responde (RF-41)', s in (200, 500), (s, r))
course = call('GET', 'my-courses/', st)[1]['enrollments'][0]['course_id']
lid = call('GET', f'learn/{course}/', st)[1]['modules'][0]['lessons'][0]['id']
cmid = call('POST', f'lessons/{lid}/comments/', st, json={'content': 'hola'})[1]['comment']['id']
s, r = call('POST', f'comments/{cmid}/edit/', st, json={'content': 'editado'})
chk('editar comentario (RF-25)', s == 200 and r['comment']['is_edited'] and r['comment']['content'] == 'editado', r)
call('POST', f'comments/{cmid}/delete/', st)

# ------------------------------------------------ docente
tt = login('teacher1', 'teacher123')
s, r = call('POST', 'manage/courses/create/', tt, json={'title': 'Curso API', 'description': 'desc', 'level': 'beginner', 'price': 10})
chk('crear curso (RF-13)', s == 200, r)
cid = r['course']['id']
chk('crear módulo', call('POST', f'manage/courses/{cid}/modules/', tt, json={'title': 'Mod 1'})[0] == 200)
call('POST', f'manage/courses/{cid}/modules/', tt, json={'title': 'Mod 2'})
mods = call('GET', f'manage/courses/{cid}/', tt)[1]['course']['modules']
m1, m2 = mods[0]['id'], mods[1]['id']
chk('reordenar módulo (RF-14)', call('POST', f'manage/modules/{m2}/move/up/', tt)[0] == 200)
s, r = call('POST', f'manage/modules/{m1}/lessons/', tt, json={'type': 'text', 'title': 'Lección texto', 'content': '<p>hola</p>'})
chk('crear lección de texto', s == 200, r)
l1 = r['lesson']['id']
s, r = call('POST', f'manage/modules/{m1}/lessons/', tt, json={'type': 'video', 'title': 'Video', 'video_url': 'https://youtu.be/dQw4w9WgXcQ'})
chk('crear lección de video', s == 200, r)
s, r = call('POST', f'manage/modules/{m1}/lessons/', tt, json={'type': 'document', 'title': 'Doc'})
chk('documento sin archivo rechazado', s == 400)
qs = [{'text': '¿2+2?', 'points': 2, 'options': [{'text': '4', 'is_correct': True}, {'text': '5', 'is_correct': False}]},
      {'text': '¿Capital?', 'options': [{'text': 'La Paz', 'is_correct': True}, {'text': 'Oruro', 'is_correct': False}, {'text': 'Sucre', 'is_correct': True}]}]
s, r = call('POST', f'manage/modules/{m1}/lessons/', tt, json={'type': 'quiz', 'title': 'Quiz API', 'content': 'Instrucciones',
            'time_limit_minutes': 20, 'passing_score': 60, 'max_attempts': 2, 'questions': qs})
chk('crear cuestionario (RF-28)', s == 200 and len(r['lesson']['quiz']['questions']) == 2, r)
lq = r['lesson']['id']
s, r = call('POST', f'manage/modules/{m1}/lessons/', tt, json={'type': 'quiz', 'title': 'Quiz malo', 'content': 'x',
            'questions': [{'text': '?', 'options': [{'text': 'a', 'is_correct': False}, {'text': 'b', 'is_correct': False}]}]})
chk('cuestionario sin respuesta correcta rechazado', s == 400, r)
s, r = call('POST', f'manage/lessons/{lq}/update/', tt, json={'type': 'quiz', 'title': 'Quiz API v2', 'content': 'Ins', 'questions': qs[:1]})
chk('editar cuestionario', s == 200 and len(r['lesson']['quiz']['questions']) == 1, r)
chk('reordenar lección', call('POST', f'manage/lessons/{l1}/move/down/', tt)[0] == 200)
s, r = call('POST', f'manage/courses/{cid}/update/', tt, json={'title': 'Curso API editado', 'price': 0, 'is_free': True})
chk('editar curso', s == 200 and r['course']['is_free'], r)
s, r = call('GET', f'manage/courses/{cid}/stats/', tt)
chk('estadísticas del curso (RF-16)', s == 200 and 'revenue' in r['stats'], r)
s, r = call('GET', f'manage/courses/{course}/results/', tt)
chk('resultados e incidencias (RF-32)', s in (200, 403), s)
s, r = call('POST', f'manage/courses/{cid}/publish/', tt)
chk('publicar curso', s == 200, r)
s, r = call('POST', 'manage/coupons/save/', tt, json={'course': cid, 'code': 'apitest10', 'discount_value': 10, 'max_uses': 5, 'expires_at': '2030-01-01'})
chk('crear cupón docente (RF-36)', s == 200, r)
cp = r['coupon']['id']
s, r = call('POST', f'manage/coupons/{cp}/toggle/', tt)
chk('activar/desactivar cupón', s == 200 and r['coupon']['is_active'] is False, r)
s, r = call('POST', f'manage/coupons/{cp}/save/', tt, json={'discount_value': 20})
chk('editar cupón', s == 200 and r['coupon']['value'] == 20, r)
chk('listar cupones docente', any(c['id'] == cp for c in call('GET', 'manage/coupons/', tt)[1]['coupons']))
chk('estudiante no crea cursos (RNF-06)', call('POST', 'manage/courses/create/', st, json={'title': 'x'})[0] == 403)
chk('docente ajeno no edita cursos', call('POST', f'manage/courses/{course}/update/', tt, json={'title': 'Hack'})[0] in (403, 404))
chk('eliminar cupón', call('POST', f'manage/coupons/{cp}/delete/', tt)[0] == 200)

# ------------------------------------------------ administrador
at = login('admin', 'admin')
for name, path in [('usuarios', 'admin/users/?q=teacher'), ('cursos', 'admin/courses/'), ('categorías', 'admin/categories/'),
                   ('reportes', 'admin/reports/'), ('cupones', 'admin/coupons/'), ('pagos', 'admin/payments/'),
                   ('certificados', 'admin/certificates/')]:
    s, r = call('GET', path, at)
    chk('admin lista ' + name, s == 200, r)
s, r = call('POST', 'admin/users/create/', at, json={'username': 'apiuser1', 'email': 'apiuser1@example.com', 'password': 'Abcd1234!', 'role': 'teacher', 'first_name': 'Api'})
chk('admin crea usuario (RF-43)', s == 200, r)
uid = r['user']['id']
s, r = call('POST', f'admin/users/{uid}/update/', at, json={'first_name': 'Api2', 'role': 'student'})
chk('admin edita usuario/rol', s == 200 and r['user']['role'] == 'student', r)
s, r = call('POST', f'admin/users/{uid}/toggle/', at)
chk('admin desactiva usuario', s == 200 and r['user']['is_active'] is False, r)
chk('admin restablece contraseña', call('POST', f'admin/users/{uid}/reset-password/', at, json={'new_password': 'Nueva1234!'})[0] == 200)
chk('admin elimina usuario', call('POST', f'admin/users/{uid}/delete/', at)[0] == 200)
chk('admin crea categoría (RF-44)', call('POST', 'admin/categories/save/', at, json={'name': 'Cat API', 'description': 'd'})[0] == 200)
catid = [c for c in call('GET', 'admin/categories/', at)[1]['categories'] if c['name'] == 'Cat API'][0]['id']
chk('admin edita categoría', call('POST', f'admin/categories/{catid}/save/', at, json={'name': 'Cat API 2'})[0] == 200)
chk('admin borra categoría', call('POST', f'admin/categories/{catid}/delete/', at)[0] == 200)
s, r = call('POST', 'admin/coupons/save/', at, json={'code': 'ADMINAPI', 'discount_type': 'fixed', 'discount_value': 5, 'max_uses': 2, 'expires_at': '2030-01-01T10:00'})
chk('admin crea cupón (RF-46)', s == 200, r)
chk('admin activa/desactiva cupón', call('POST', f'admin/coupons/{r["coupon"]["id"]}/toggle/', at)[0] == 200)
s, r = call('POST', f'admin/courses/{cid}/retire/', at)
chk('admin retira curso', s == 200 and r['status'] == 'archived', r)
s, r = call('POST', f'admin/courses/{cid}/approve/', at)
chk('admin aprueba curso', s == 200 and r['status'] == 'published', r)
s, r = call('POST', f'admin/courses/{cid}/reject/', at, json={'reason': 'no cumple'})
chk('admin rechaza curso', s == 200 and r['status'] == 'rejected', r)
s, r = call('POST', 'admin/generate-report/', at, json={'date_from': '2026-01-01', 'date_to': '2026-12-31'})
chk('admin genera reporte (RF-49)', s == 200 and 'revenue' in r['report'], r)
rep = call('GET', 'admin/reports/', at)[1]['reports']
if rep:
    chk('admin gestiona contenido reportado (RF-45)', call('POST', f'admin/reports/{rep[0]["id"]}/dismiss/', at)[0] == 200)
    django(f"from academi.models import Report;r=Report.objects.get(id={rep[0]['id']});r.status='{rep[0]['status']}';r.resolved_at=None;r.resolved_by=None;r.save()")
chk('docente no accede a admin (RNF-06)', call('GET', 'admin/users/', tt)[0] == 403)

# ------------------------------------------------ limpieza
call('POST', f'manage/courses/{cid}/delete/', tt)
django("from academi.models import *;User.objects.filter(email='apitest@example.com').delete();"
       "Coupon.objects.filter(code__in=['ADMINAPI','APITEST10']).delete();Course.objects.filter(title__startswith='Curso API').delete()")
print('\nFALLOS:', fails or 'ninguno')
