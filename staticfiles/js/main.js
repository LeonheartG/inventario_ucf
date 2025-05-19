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
});