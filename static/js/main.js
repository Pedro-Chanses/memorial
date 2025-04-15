// Ініціалізація підказок Bootstrap
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Анімація появи елементів при прокрутці
function handleScrollAnimation() {
    const elements = document.querySelectorAll('.fade-in');
    elements.forEach(element => {
        const elementTop = element.getBoundingClientRect().top;
        const windowHeight = window.innerHeight;
        if (elementTop < windowHeight * 0.9) {
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }
    });
}

window.addEventListener('scroll', handleScrollAnimation);
window.addEventListener('load', handleScrollAnimation);

// Обробка форм
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('is-invalid');
                } else {
                    field.classList.remove('is-invalid');
                }
            });

            if (!isValid) {
                e.preventDefault();
            }
        });
    });
});

// Обробка завантаження зображень
function handleImageUpload(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        const preview = document.querySelector('#imagePreview');
        
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        };
        
        reader.readAsDataURL(input.files[0]);
    }
}

// Лічильник символів для текстових полів
function updateCharCount(textarea, counter) {
    const maxLength = textarea.getAttribute('maxlength');
    const currentLength = textarea.value.length;
    counter.textContent = `${currentLength}/${maxLength}`;
}

// Ініціалізація лічильників символів
document.addEventListener('DOMContentLoaded', function() {
    const textareas = document.querySelectorAll('textarea[maxlength]');
    textareas.forEach(textarea => {
        const counter = document.createElement('small');
        counter.classList.add('text-muted', 'char-counter');
        textarea.parentNode.insertBefore(counter, textarea.nextSibling);
        
        updateCharCount(textarea, counter);
        textarea.addEventListener('input', () => updateCharCount(textarea, counter));
    });
});

// Фільтрація та сортування проектів
function filterProjects(category) {
    const projects = document.querySelectorAll('.project-card');
    projects.forEach(project => {
        if (category === 'all' || project.dataset.category === category) {
            project.style.display = 'block';
        } else {
            project.style.display = 'none';
        }
    });
}

function sortProjects(criteria) {
    const projectsContainer = document.querySelector('.projects-container');
    const projects = Array.from(projectsContainer.children);
    
    projects.sort((a, b) => {
        const valueA = a.dataset[criteria];
        const valueB = b.dataset[criteria];
        
        if (criteria === 'date') {
            return new Date(valueB) - new Date(valueA);
        }
        return valueB - valueA;
    });
    
    projects.forEach(project => projectsContainer.appendChild(project));
}

// Обробка модальних вікон
function handleModal(modalId, action) {
    const modal = document.querySelector(modalId);
    const modalInstance = bootstrap.Modal.getInstance(modal);
    
    if (action === 'show') {
        new bootstrap.Modal(modal).show();
    } else if (action === 'hide' && modalInstance) {
        modalInstance.hide();
    }
}
