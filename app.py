from flask import Flask, render_template, request, send_file
from docxtpl import DocxTemplate
from io import BytesIO
import pdfkit
import os
import re
import shutil
import tempfile
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _find_wkhtmltopdf():
    # Look for an explicit environment variable first, then try PATH
    env_path = os.environ.get('WKHTMLTOPDF_PATH')
    if env_path and os.path.isfile(env_path):
        return env_path
    path = shutil.which('wkhtmltopdf')
    return path


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    form_data = request.form

    # Normalize and clean up simple fields
    skills = [s.strip() for s in form_data.get('skills', '').split(',') if s.strip()]

    template_data = {
        'name': form_data.get('name', '').strip(),
        'email': form_data.get('email', '').strip(),
        'address': form_data.get('address', '').strip(),
        'phone': form_data.get('phone', '').strip(),
        'linkedin': form_data.get('linkedin', '').strip(),
        'summary': form_data.get('summary', '').strip(),
        'experiences': [],
        'educations': [],
        'skills_list': skills,
    }

    # Collect experience entries by detecting numbered keys (handles gaps)
    exp_indices = set()
    for key in form_data.keys():
        m = re.match(r'jobTitle(\d+)$', key)
        if m:
            exp_indices.add(int(m.group(1)))

    for i in sorted(exp_indices):
        job_title = form_data.get(f'jobTitle{i}')
        if not job_title:
            continue
        template_data['experiences'].append({
            'job_title': job_title.strip(),
            'company': form_data.get(f'company{i}', '').strip(),
            'dates': form_data.get(f'datesExp{i}', '').strip(),
            'description': form_data.get(f'description{i}', '').strip(),
        })

    # Collect education entries similarly
    edu_indices = set()
    for key in form_data.keys():
        m = re.match(r'degree(\d+)$', key)
        if m:
            edu_indices.add(int(m.group(1)))

    for i in sorted(edu_indices):
        degree = form_data.get(f'degree{i}')
        if not degree:
            continue
        template_data['educations'].append({
            'degree': degree.strip(),
            'institution': form_data.get(f'institution{i}', '').strip(),
            'dates': form_data.get(f'datesEdu{i}', '').strip(),
            'cgpa': form_data.get(f'cgpa{i}', '').strip(),
        })

    # Determine requested format (be tolerant of exact button labels)
    fmt_raw = form_data.get('format', '')
    fmt = fmt_raw.strip().lower()

    # DOCX generation
    if 'docx' in fmt:
        # Look for docx_template.docx in templates/ first, then repo root
        possible_paths = [
            os.path.join(app.root_path, 'templates', 'docx_template.docx'),
            os.path.join(app.root_path, 'docx_template.docx'),
        ]
        template_path = None
        for p in possible_paths:
            if os.path.exists(p):
                template_path = p
                break

        if not template_path:
            logger.error('DOCX template not found at %s', possible_paths)
            return 'DOCX template (docx_template.docx) not found on server.', 500

        try:
            tpl = DocxTemplate(template_path)
            tpl.render(template_data)

            # Try to save to an in-memory BytesIO. docxtpl/python-docx sometimes accepts file-like objects.
            file_stream = BytesIO()
            try:
                tpl.save(file_stream)
                file_stream.seek(0)
            except TypeError:
                # Fallback: save to a temp file and read it back
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
                tmp_path = tmp.name
                tmp.close()
                tpl.save(tmp_path)
                with open(tmp_path, 'rb') as fh:
                    file_stream.write(fh.read())
                os.unlink(tmp_path)
                file_stream.seek(0)

            return send_file(
                file_stream,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                as_attachment=True,
                download_name='resume.docx'
            )

        except Exception as e:
            logger.exception('Error generating DOCX')
            return f'DOCX generation failed: {e}', 500

    # PDF generation
    if 'pdf' in fmt:
        # Render the HTML template used for PDF
        try:
            html = render_template('pdf_template.html', data=template_data)
        except Exception as e:
            logger.exception('Error rendering PDF template')
            return f'PDF template rendering failed: {e}', 500

        wk_path = _find_wkhtmltopdf()
        config = None
        if wk_path:
            config = pdfkit.configuration(wkhtmltopdf=wk_path)
        else:
            logger.warning('wkhtmltopdf not found on PATH and WKHTMLTOPDF_PATH not set')

        try:
            # Passing False as output_path returns bytes
            pdf_bytes = pdfkit.from_string(html, False, configuration=config)
            if not pdf_bytes:
                raise RuntimeError('pdfkit returned empty content')
            pdf_file = BytesIO(pdf_bytes)
            pdf_file.seek(0)
            return send_file(
                pdf_file,
                mimetype='application/pdf',
                as_attachment=True,
                download_name='resume.pdf'
            )
        except Exception as e:
            logger.exception('PDF generation error')
            return f'PDF generation failed: {e}', 500

    return 'Format not specified', 400


if __name__ == '__main__':
    # Honor FLASK_DEBUG environment variable; default to True for development
    debug_env = os.environ.get('FLASK_DEBUG', '1')
    debug = debug_env == '1' or debug_env.lower() == 'true'
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=debug)
