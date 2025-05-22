// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Animación para mensajes de alerta
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        // Añadir clase para animación
        alert.classList.add('fade-in');
        
        // Auto-cerrar alertas después de 5 segundos
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);
    });
    
    // Activar todos los tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Efecto hover para los elementos de navegación
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.style.transition = 'transform 0.3s';
            this.style.transform = 'translateY(-2px)';
        });
        
        link.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Validaciones de formularios
    initFormValidations();
    
    // Funcionalidad específica para registro
    if (document.getElementById('id_password2')) {
        initPasswordValidation();
    }
});

// Inicializar validaciones de formularios
function initFormValidations() {
    // Limpiar errores al escribir en los campos
    const formControls = document.querySelectorAll('.form-control');
    formControls.forEach(input => {
        input.addEventListener('input', function() {
            // Remover clases de error
            this.classList.remove('is-invalid');
            
            // Ocultar mensajes de error
            const errorMsg = this.parentNode.querySelector('.text-danger');
            if (errorMsg) {
                errorMsg.style.display = 'none';
            }
        });
    });

    // Auto-focus en el primer campo con error
    const firstError = document.querySelector('.is-invalid');
    if (firstError) {
        firstError.focus();
    }
}

// Validación de contraseñas en tiempo real
function initPasswordValidation() {
    const password1 = document.getElementById('id_password1');
    const password2 = document.getElementById('id_password2');
    
    if (password1 && password2) {
        password2.addEventListener('input', function() {
            validatePasswordMatch();
        });
        
        password1.addEventListener('input', function() {
            validatePasswordMatch();
        });
    }
}

// Validar que las contraseñas coincidan
function validatePasswordMatch() {
    const password1 = document.getElementById('id_password1');
    const password2 = document.getElementById('id_password2');
    
    if (password1.value && password2.value) {
        if (password1.value === password2.value) {
            password2.classList.remove('is-invalid');
            password2.classList.add('is-valid');
            
            // Ocultar mensaje de error si existe
            const errorMsg = password2.parentNode.querySelector('.text-danger');
            if (errorMsg) {
                errorMsg.style.display = 'none';
            }
            
            // Mostrar mensaje de éxito
            showPasswordMatchFeedback(true);
        } else {
            password2.classList.remove('is-valid');
            password2.classList.add('is-invalid');
            showPasswordMatchFeedback(false);
        }
    } else {
        password2.classList.remove('is-valid', 'is-invalid');
        hidePasswordMatchFeedback();
    }
}

// Mostrar feedback de coincidencia de contraseñas
function showPasswordMatchFeedback(isMatch) {
    const password2 = document.getElementById('id_password2');
    let feedback = password2.parentNode.querySelector('.password-match-feedback');
    
    if (!feedback) {
        feedback = document.createElement('div');
        feedback.className = 'password-match-feedback small mt-1';
        password2.parentNode.appendChild(feedback);
    }
    
    if (isMatch) {
        feedback.className = 'password-match-feedback small mt-1 text-success';
        feedback.innerHTML = '<i class="fas fa-check-circle me-1"></i>Las contraseñas coinciden';
    } else {
        feedback.className = 'password-match-feedback small mt-1 text-danger';
        feedback.innerHTML = '<i class="fas fa-times-circle me-1"></i>Las contraseñas no coinciden';
    }
}

// Ocultar feedback de contraseñas
function hidePasswordMatchFeedback() {
    const feedback = document.querySelector('.password-match-feedback');
    if (feedback) {
        feedback.remove();
    }
}

// Función para mostrar/ocultar contraseñas (opcional)
function togglePassword(fieldId) {
    const passwordField = document.getElementById(fieldId);
    const toggleBtn = passwordField.parentNode.querySelector('.password-toggle');
    
    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        if (toggleBtn) {
            toggleBtn.innerHTML = '<i class="fas fa-eye-slash"></i>';
        }
    } else {
        passwordField.type = 'password';
        if (toggleBtn) {
            toggleBtn.innerHTML = '<i class="fas fa-eye"></i>';
        }
    }
}

// Validación de email en tiempo real (opcional)
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Validación de username en tiempo real (opcional)
function validateUsername(username) {
    // Mínimo 3 caracteres, solo letras, números, puntos, guiones y guiones bajos
    const usernameRegex = /^[a-zA-Z0-9._-]{3,}$/;
    return usernameRegex.test(username);
}