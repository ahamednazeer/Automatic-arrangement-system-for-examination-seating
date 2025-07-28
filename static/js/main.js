// Modern JavaScript for Exam Seating System

class ExamSeatApp {
    constructor() {
        this.init();
    }

    init() {
        this.setupSidebar();
        this.setupUserMenu();
        this.setupFlashMessages();
        this.setupFormValidation();
        this.setupDataTables();
        this.setupModals();
        this.setupTooltips();
        this.setupSearchFilters();
    }

    // Sidebar functionality
    setupSidebar() {
        const sidebar = document.getElementById('sidebar');
        const sidebarToggle = document.getElementById('sidebarToggle');
        const mobileSidebarToggle = document.getElementById('mobileSidebarToggle');
        const mainContent = document.getElementById('mainContent');

        // Mobile sidebar toggle
        if (mobileSidebarToggle) {
            mobileSidebarToggle.addEventListener('click', () => {
                sidebar.classList.toggle('active');
                this.toggleBodyOverflow();
            });
        }

        // Desktop sidebar toggle
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                sidebar.classList.toggle('collapsed');
                mainContent.classList.toggle('sidebar-collapsed');
            });
        }

        // Close sidebar on outside click (mobile)
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 1024) {
                if (!sidebar.contains(e.target) && !mobileSidebarToggle.contains(e.target)) {
                    sidebar.classList.remove('active');
                    this.toggleBodyOverflow();
                }
            }
        });

        // Handle window resize
        window.addEventListener('resize', () => {
            if (window.innerWidth > 1024) {
                sidebar.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    }

    toggleBodyOverflow() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar.classList.contains('active')) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
    }

    // User menu dropdown
    setupUserMenu() {
        const userMenu = document.querySelector('.user-menu');
        const dropdownMenu = document.querySelector('.dropdown-menu');

        if (userMenu && dropdownMenu) {
            userMenu.addEventListener('click', (e) => {
                e.stopPropagation();
                dropdownMenu.classList.toggle('show');
            });

            document.addEventListener('click', () => {
                dropdownMenu.classList.remove('show');
            });
        }
    }

    // Flash messages auto-hide
    setupFlashMessages() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            // Auto-hide after 5 seconds
            setTimeout(() => {
                this.fadeOut(alert);
            }, 5000);

            // Close button functionality
            const closeBtn = alert.querySelector('.alert-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    this.fadeOut(alert);
                });
            }
        });
    }

    fadeOut(element) {
        element.style.opacity = '0';
        element.style.transform = 'translateY(-20px)';
        setTimeout(() => {
            element.remove();
        }, 300);
    }

    // Form validation
    setupFormValidation() {
        const forms = document.querySelectorAll('form[data-validate]');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                }
            });

            // Real-time validation
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.addEventListener('blur', () => {
                    this.validateField(input);
                });
            });
        });
    }

    validateForm(form) {
        let isValid = true;
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        
        inputs.forEach(input => {
            if (!this.validateField(input)) {
                isValid = false;
            }
        });

        return isValid;
    }

    validateField(field) {
        const value = field.value.trim();
        const fieldGroup = field.closest('.form-group');
        let isValid = true;
        let errorMessage = '';

        // Remove existing error
        this.removeFieldError(fieldGroup);

        // Required validation
        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = 'This field is required';
        }

        // Email validation
        if (field.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                errorMessage = 'Please enter a valid email address';
            }
        }

        // Phone validation
        if (field.type === 'tel' && value) {
            const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
            if (!phoneRegex.test(value.replace(/\s/g, ''))) {
                isValid = false;
                errorMessage = 'Please enter a valid phone number';
            }
        }

        // Number validation
        if (field.type === 'number' && value) {
            const min = field.getAttribute('min');
            const max = field.getAttribute('max');
            const numValue = parseFloat(value);

            if (min && numValue < parseFloat(min)) {
                isValid = false;
                errorMessage = `Value must be at least ${min}`;
            }
            if (max && numValue > parseFloat(max)) {
                isValid = false;
                errorMessage = `Value must be at most ${max}`;
            }
        }

        if (!isValid) {
            this.showFieldError(fieldGroup, errorMessage);
            field.classList.add('is-invalid');
        } else {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        }

        return isValid;
    }

    showFieldError(fieldGroup, message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        errorDiv.textContent = message;
        fieldGroup.appendChild(errorDiv);
    }

    removeFieldError(fieldGroup) {
        const existingError = fieldGroup.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }
    }

    // Data tables functionality
    setupDataTables() {
        const tables = document.querySelectorAll('.data-table');
        tables.forEach(table => {
            this.enhanceTable(table);
        });
    }

    enhanceTable(table) {
        // Add sorting functionality
        const headers = table.querySelectorAll('th[data-sortable]');
        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                this.sortTable(table, header);
            });
        });

        // Add search functionality if search input exists
        const searchInput = document.querySelector(`[data-table-search="${table.id}"]`);
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterTable(table, e.target.value);
            });
        }
    }

    sortTable(table, header) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const columnIndex = Array.from(header.parentNode.children).indexOf(header);
        const isAscending = header.classList.contains('sort-asc');

        rows.sort((a, b) => {
            const aText = a.children[columnIndex].textContent.trim();
            const bText = b.children[columnIndex].textContent.trim();
            
            // Try to parse as numbers
            const aNum = parseFloat(aText);
            const bNum = parseFloat(bText);
            
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return isAscending ? bNum - aNum : aNum - bNum;
            }
            
            return isAscending ? bText.localeCompare(aText) : aText.localeCompare(bText);
        });

        // Clear all sort classes
        table.querySelectorAll('th').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
        });

        // Add appropriate sort class
        header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');

        // Reorder rows
        rows.forEach(row => tbody.appendChild(row));
    }

    filterTable(table, searchTerm) {
        const tbody = table.querySelector('tbody');
        const rows = tbody.querySelectorAll('tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const matches = text.includes(searchTerm.toLowerCase());
            row.style.display = matches ? '' : 'none';
        });
    }

    // Modal functionality
    setupModals() {
        const modalTriggers = document.querySelectorAll('[data-modal]');
        modalTriggers.forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                e.preventDefault();
                const modalId = trigger.getAttribute('data-modal');
                this.openModal(modalId);
            });
        });

        const modalCloses = document.querySelectorAll('[data-modal-close]');
        modalCloses.forEach(close => {
            close.addEventListener('click', () => {
                this.closeModal(close.closest('.modal'));
            });
        });

        // Close modal on outside click
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal(e.target);
            }
        });
    }

    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
            setTimeout(() => {
                modal.classList.add('show');
            }, 10);
        }
    }

    closeModal(modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }, 300);
    }

    // Tooltip functionality
    setupTooltips() {
        const tooltipTriggers = document.querySelectorAll('[data-tooltip]');
        tooltipTriggers.forEach(trigger => {
            trigger.addEventListener('mouseenter', (e) => {
                this.showTooltip(e.target);
            });
            trigger.addEventListener('mouseleave', (e) => {
                this.hideTooltip(e.target);
            });
        });
    }

    showTooltip(element) {
        const text = element.getAttribute('data-tooltip');
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = text;
        document.body.appendChild(tooltip);

        const rect = element.getBoundingClientRect();
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';

        element._tooltip = tooltip;
    }

    hideTooltip(element) {
        if (element._tooltip) {
            element._tooltip.remove();
            delete element._tooltip;
        }
    }

    // Search and filter functionality
    setupSearchFilters() {
        const filterForms = document.querySelectorAll('.filter-form');
        filterForms.forEach(form => {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.applyFilters(form);
            });

            // Auto-apply filters on input change
            const inputs = form.querySelectorAll('input, select');
            inputs.forEach(input => {
                input.addEventListener('change', () => {
                    this.applyFilters(form);
                });
            });
        });
    }

    applyFilters(form) {
        const formData = new FormData(form);
        const params = new URLSearchParams();
        
        for (let [key, value] of formData.entries()) {
            if (value.trim()) {
                params.append(key, value);
            }
        }

        // Update URL without page reload
        const newUrl = window.location.pathname + '?' + params.toString();
        window.history.pushState({}, '', newUrl);

        // Reload content (you might want to use AJAX here)
        window.location.reload();
    }

    // Utility functions
    showLoading(element) {
        element.classList.add('loading');
        element.disabled = true;
    }

    hideLoading(element) {
        element.classList.remove('loading');
        element.disabled = false;
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
            <button class="alert-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;

        const container = document.querySelector('.flash-messages') || document.querySelector('.content');
        container.insertBefore(notification, container.firstChild);

        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.fadeOut(notification);
        }, 5000);
    }

    // AJAX helper
    async makeRequest(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const config = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Request failed');
            }

            return data;
        } catch (error) {
            this.showNotification(error.message, 'error');
            throw error;
        }
    }

    // File upload helper
    setupFileUpload() {
        const fileInputs = document.querySelectorAll('input[type="file"]');
        fileInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                this.handleFileUpload(e.target);
            });
        });
    }

    handleFileUpload(input) {
        const file = input.files[0];
        if (!file) return;

        // Validate file type
        const allowedTypes = input.getAttribute('accept');
        if (allowedTypes && !allowedTypes.split(',').some(type => file.type.includes(type.trim()))) {
            this.showNotification('Invalid file type', 'error');
            input.value = '';
            return;
        }

        // Validate file size (16MB max)
        const maxSize = 16 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showNotification('File size too large (max 16MB)', 'error');
            input.value = '';
            return;
        }

        // Show file info
        const fileInfo = input.parentNode.querySelector('.file-info');
        if (fileInfo) {
            fileInfo.textContent = `Selected: ${file.name} (${this.formatFileSize(file.size)})`;
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.examSeatApp = new ExamSeatApp();
});

// Additional utility functions for specific features

// Seating arrangement visualization
function renderSeatingChart(roomData, seatingData) {
    const container = document.getElementById('seating-chart');
    if (!container) return;

    container.innerHTML = '';
    
    const grid = document.createElement('div');
    grid.className = 'seating-grid';
    grid.style.gridTemplateColumns = `repeat(${roomData.cols}, 1fr)`;
    grid.style.gridTemplateRows = `repeat(${roomData.rows}, 1fr)`;

    for (let row = 1; row <= roomData.rows; row++) {
        for (let col = 1; col <= roomData.cols; col++) {
            const seat = document.createElement('div');
            seat.className = 'seat';
            seat.dataset.row = row;
            seat.dataset.col = col;

            const student = seatingData.find(s => s.seat_row === row && s.seat_col === col);
            if (student) {
                seat.classList.add('occupied');
                seat.innerHTML = `
                    <div class="seat-number">${row}-${col}</div>
                    <div class="student-id">${student.student_id}</div>
                `;
                seat.title = `${student.student_name} - ${student.subject_code}`;
            } else {
                seat.classList.add('empty');
                seat.innerHTML = `<div class="seat-number">${row}-${col}</div>`;
            }

            grid.appendChild(seat);
        }
    }

    container.appendChild(grid);
}

// Export functions
function exportToCSV(data, filename) {
    const csv = data.map(row => 
        Object.values(row).map(value => 
            typeof value === 'string' && value.includes(',') ? `"${value}"` : value
        ).join(',')
    ).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

function exportToPDF(elementId, filename) {
    const element = document.getElementById(elementId);
    if (!element) return;

    // You would typically use a library like jsPDF here
    // For now, we'll use the browser's print functionality
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
            <head>
                <title>${filename}</title>
                <style>
                    body { font-family: Arial, sans-serif; }
                    .seating-grid { display: grid; gap: 2px; }
                    .seat { border: 1px solid #ccc; padding: 5px; text-align: center; }
                    .occupied { background-color: #e3f2fd; }
                    .empty { background-color: #f5f5f5; }
                </style>
            </head>
            <body>
                ${element.outerHTML}
            </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.print();
}