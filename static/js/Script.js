document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('resumeForm');
    const preview = document.getElementById('resumePreview');

    form.addEventListener('input', updatePreview);

    form.addEventListener('submit', function(event) {
        event.preventDefault();
        updatePreview();

        const format = event.submitter.value;

        fetch('/generate', {
            method: 'POST',
            body: new FormData(form)
        })
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `resume.${format.split(" ")[1].toLowerCase()}`; // Correct filename!
            document.body.appendChild(a); // Ensure link is in DOM
            a.click();
            window.URL.revokeObjectURL(url);
        });
    });

    function updatePreview() {
        const formData = new FormData(form);
        let previewHTML = '';

        previewHTML += `
            <div class="header">
                <div class="name">${formData.get('name') || ''}</div>
                <div class="contact-info">
                    ${formData.get('address') ? '<p>' + formData.get('address') + '</p>' : ''}
                    ${formData.get('phone') ? '<p>Phone: ' + formData.get('phone') + '</p>' : ''}
                    ${formData.get('email') ? '<p>Email: <a href="mailto:' + formData.get('email') + '">' + formData.get('email') + '</a></p>' : ''}
                    ${formData.get('linkedin') ? '<p>LinkedIn: <a href="' + formData.get('linkedin') + '" target="_blank">' + formData.get('linkedin') + '</a></p>' : ''}
                </div>
            </div>

            <div class="section">
                <div class="section-title">Summary</div>
                <div class="entry">${formData.get('summary') || ''}</div>
            </div>

            <div class="section">
                <div class="section-title">Experience</div>
                <div class="entry experience-entry">
                    <div class="experience-title">${formData.get('jobTitle1') || ''}, ${formData.get('company1') || ''}</div>
                    <div class="experience-dates">${formData.get('datesExp1') || ''}</div>
                    <div class="experience-description">${formData.get('description1') || ''}</div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Education</div>
                <div class="entry education-entry">
                    <div class="education-degree">${formData.get('degree1') || ''}</div>
                    <div class="education-institution">${formData.get('institution1') || ''}</div>
                    <div class="education-dates">${formData.get('datesEdu1') || ''}</div>
                    <div class="education-cgpa">CGPA: ${formData.get('cgpa1') || ''}</div>
                </div>
                <div class="entry education-entry">
                    <div class="education-degree">${formData.get('degree2') || ''}</div>
                    <div class="education-institution">${formData.get('institution2') || ''}</div>
                    <div class="education-dates">${formData.get('datesEdu2') || ''}</div>
                    <div class="education-cgpa">CGPA: ${formData.get('cgpa2') || ''}</div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Skills</div>
                <div class="entry skills-list">
                    ${(formData.get('skills') || '').split(',').map(skill => `<div class="skills-item">${skill.trim()}</div>`).join('')}
                </div>
            </div>
        `;

        preview.innerHTML = previewHTML;
    }

    updatePreview();
});