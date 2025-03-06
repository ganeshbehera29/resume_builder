from flask import Flask, render_template, request, send_file
from docx.templates import DocxTemplate
from io import BytesIO
import pdfkit

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    form_data = request.form

    template_data = {
        'name': form_data.get('name', ''),
        'email': form_data.get('email', ''),
        'address': form_data.get('address', ''),
        'phone': form_data.get('phone', ''),
        'linkedin': form_data.get('linkedin', ''),
        'summary': form_data.get('summary', ''),
        'experiences': [],
        'educations': [],
        'skills_list': form_data.get('skills', '').split(','),
    }

    i = 1
    while True:
        job_title = form_data.get(f'jobTitle{i}')
        if not job_title:
            break
        template_data['experiences'].append({
            'job_title': job_title,
            'company': form_data.get(f'company{i}'),
            'dates': form_data.get(f'datesExp{i}'),
            'description': form_data.get(f'description{i}')
        })
        i += 1

    i = 1
    while True:
        degree = form_data.get(f'degree{i}')
        if not degree:
            break
        template_data['educations'].append({
            'degree': degree,
            'institution': form_data.get(f'institution{i}'),
            'dates': form_data.get(f'datesEdu{i}'),
            'cgpa': form_data.get(f'cgpa{i}')
        })
        i += 1

    if 'format' in form_data:
        if form_data['format'] == 'Generate Docx':
            template = DocxTemplate("docx_template.docx")
            template.render(template_data)
            file_stream = BytesIO()
            template.save(file_stream)
            file_stream.seek(0)
            return send_file(
                file_stream,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                as_attachment=True,
                download_name='resume.docx'
            )

        elif form_data['format'] == 'Generate PDF':
            html = render_template('pdf_template.html', data=template_data)
            pdf_file = BytesIO()
            try:
                pdfkit.from_string(html, pdf_file)
                pdf_file.seek(0)
                return send_file(
                    pdf_file,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name='resume.pdf'
                )
            except Exception as e:
                print(f"PDF Generation Error: {e}")
                return f"PDF generation failed: {e}", 500

    else:
        return "Format not specified", 400

if __name__ == '__main__':
    app.run(debug=True)