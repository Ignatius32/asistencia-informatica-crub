// This file contains JavaScript for client-side functionality.

document.addEventListener('DOMContentLoaded', function() {
    // Ticket search and filtering functionality
    const ticketSearch = document.getElementById('ticketSearch');
    const statusFilter = document.getElementById('statusFilter');
    const ticketRows = document.querySelectorAll('.ticket-row');

    function filterTickets() {
        const searchTerm = ticketSearch.value.toLowerCase();
        const statusTerm = statusFilter.value.toLowerCase();

        ticketRows.forEach(row => {
            const description = row.querySelector('.ticket-description').textContent.toLowerCase();
            const status = row.querySelector('.status-badge').textContent.toLowerCase();
            
            const matchesSearch = description.includes(searchTerm);
            const matchesStatus = !statusTerm || status.includes(statusTerm);
            
            row.style.display = (matchesSearch && matchesStatus) ? '' : 'none';
        });
    }

    if (ticketSearch) {
        ticketSearch.addEventListener('input', filterTickets);
    }
    if (statusFilter) {
        statusFilter.addEventListener('change', filterTickets);
    }

    // Form validation and enhanced textarea
    const ticketForm = document.querySelector('.enhanced-form');
    if (ticketForm) {
        const descriptionField = ticketForm.querySelector('#description');
        
        // Auto-expand textarea
        descriptionField.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });

        // Form validation
        ticketForm.addEventListener('submit', function(e) {
            const description = descriptionField.value.trim();
            const category = ticketForm.querySelector('#category').value;
            
            if (description.length < 10) {
                e.preventDefault();
                alert('Por favor, proporcione una descripción más detallada (mínimo 10 caracteres).');
                descriptionField.focus();
            }
            
            if (!category) {
                e.preventDefault();
                alert('Por favor, seleccione una categoría.');
            }
        });
    }
});

// Handle form submissions and button clicks
document.addEventListener('click', function(e) {
    const target = e.target;
    
    // Handle form submit buttons
    if (target.type === 'submit' || target.classList.contains('btn')) {
        const form = target.closest('form');
        if (form) {
            // Don't add loading state for JavaScript validation
            if (form.classList.contains('enhanced-form') && !form.checkValidity()) {
                return;
            }
            
            // Add loading state
            target.classList.add('loading');
            form.classList.add('disabled-interaction');
            
            // Store original text
            target.dataset.originalText = target.innerHTML;
            target.innerHTML = '';
        }
    }
});

// Handle delete confirmations with loading state
document.querySelectorAll('[onclick*="confirm"]').forEach(button => {
    button.onclick = function(e) {
        if (!confirm(this.getAttribute('onclick').split("'")[1])) {
            e.preventDefault();
            return false;
        }
        this.classList.add('loading');
        return true;
    };
});

// Handle links that should show loading state (those with .btn class)
document.addEventListener('click', function(e) {
    const target = e.target;
    if (target.classList.contains('btn') && target.href && !target.onclick) {
        target.classList.add('loading');
    }
});