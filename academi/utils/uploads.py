"""RNF-19: formatos y tamaños permitidos para los archivos educativos.
Lo usan el sitio web (UploadValidationMiddleware) y la API móvil."""
import os

MB = 1024 * 1024

UPLOAD_RULES = {
    'image': ({'.jpg', '.jpeg', '.png', '.webp', '.gif'}, 5 * MB, 'imagen'),
    'video': ({'.mp4', '.webm', '.mov', '.mkv', '.m4v'}, 500 * MB, 'video'),
    'document': ({'.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt', '.zip'}, 50 * MB, 'documento'),
    'assignment': ({'.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt', '.zip', '.rar',
                    '.jpg', '.jpeg', '.png', '.py', '.java', '.c', '.cpp', '.js', '.html', '.css', '.sql'},
                   25 * MB, 'archivo'),
}

# Nombre del campo de formulario -> tipo de regla que le corresponde.
FIELD_KINDS = {
    'image': 'image', 'profile_picture': 'image',
    'video_promo': 'video', 'video_file': 'video', 'video': 'video',
    'document_file': 'document', 'document': 'document',
    'file': 'assignment',
}


def validate_upload(uploaded, kind):
    """Devuelve un mensaje de error si el archivo excede el tamaño o formato permitido."""
    extensions, max_size, label = UPLOAD_RULES[kind]
    ext = os.path.splitext(uploaded.name)[1].lower()
    if ext not in extensions:
        return f'Formato no permitido para {label}. Permitidos: {", ".join(sorted(extensions))}.'
    if uploaded.size > max_size:
        return f'El {label} supera el tamaño máximo de {max_size // MB} MB.'
    return None
