document.addEventListener('DOMContentLoaded', function() {
    // Utility function to check if a date is within a given range
    function isDateInRange(dateStr, range) {
        const date = new Date(dateStr);
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        switch(range) {
            case 'today':
                return date >= today;
            case 'week':
                const weekAgo = new Date(today);
                weekAgo.setDate(weekAgo.getDate() - 7);
                return date >= weekAgo;
            case 'month':
                const monthAgo = new Date(today);
                monthAgo.setMonth(monthAgo.getMonth() - 1);
                return date >= monthAgo;
            default:
                return true;
        }
    }

    // Generic function to filter tickets
    function filterTickets(tableId) {
        const table = document.getElementById(tableId);
        if (!table) return;

        const searchInput = document.querySelector(`.ticket-search[data-table="${tableId}"]`);
        const statusFilter = document.querySelector(`.status-filter[data-table="${tableId}"]`);
        const priorityFilter = document.querySelector(`.priority-filter[data-table="${tableId}"]`);
        const departmentFilter = document.querySelector(`.department-filter[data-table="${tableId}"]`);
        const technicianFilter = document.querySelector(`.technician-filter[data-table="${tableId}"]`);
        const dateFilter = document.querySelector(`.date-filter[data-table="${tableId}"]`);

        const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
        const statusTerm = statusFilter ? statusFilter.value : '';
        const priorityTerm = priorityFilter ? priorityFilter.value : '';
        const departmentTerm = departmentFilter ? departmentFilter.value : '';
        const technicianTerm = technicianFilter ? technicianFilter.value : '';
        const dateTerm = dateFilter ? dateFilter.value : '';

        const rows = table.querySelectorAll('tbody tr');

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const status = row.getAttribute('data-status');
            const priority = row.getAttribute('data-priority');
            const department = row.getAttribute('data-department');
            const technician = row.getAttribute('data-technician');
            const date = row.getAttribute('data-date');

            const matchesSearch = text.includes(searchTerm);
            const matchesStatus = !statusTerm || (status && status === statusTerm);
            const matchesPriority = !priorityTerm || (priority && priority === priorityTerm);
            const matchesDepartment = !departmentTerm || department === departmentTerm;
            const matchesTechnician = !technicianTerm || technician === technicianTerm;
            const matchesDate = !dateTerm || (date && isDateInRange(date, dateTerm));

            row.style.display = (matchesSearch && matchesStatus && matchesPriority && 
                               matchesDepartment && matchesTechnician && matchesDate) ? '' : 'none';
        });

        // Update counters if they exist
        updateTicketCounters(tableId);
    }

    // Update ticket counters in stat boxes
    function updateTicketCounters(tableId) {
        const table = document.getElementById(tableId);
        if (!table) return;

        const visibleRows = table.querySelectorAll('tbody tr:not([style*="display: none"])').length;
        const counterElement = document.querySelector(`[data-counter="${tableId}"]`);
        if (counterElement) {
            counterElement.textContent = visibleRows;
        }
    }

    // Attach event listeners to all filter inputs
    document.querySelectorAll('.ticket-search, .status-filter, .priority-filter, .department-filter, .technician-filter, .date-filter')
        .forEach(element => {
            const tableId = element.getAttribute('data-table');
            element.addEventListener('input', () => filterTickets(tableId));
            element.addEventListener('change', () => filterTickets(tableId));
        });

    // Initial filtering
    const tables = ['unassigned-tickets', 'open-tickets', 'in-progress-tickets', 'closed-tickets', 'all-tickets'];
    tables.forEach(tableId => {
        if (document.getElementById(tableId)) {
            filterTickets(tableId);
        }
    });

    // Export functionality for admin dashboard
    const exportBtn = document.getElementById('exportTickets');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            const table = document.getElementById('all-tickets');
            if (!table) return;

            let csv = [];
            const headers = [];
            table.querySelectorAll('thead th').forEach(th => headers.push(th.textContent.trim()));
            csv.push(headers.join(','));

            table.querySelectorAll('tbody tr:not([style*="display: none"])').forEach(row => {
                const rowData = [];
                row.querySelectorAll('td').forEach(cell => {
                    let text = cell.textContent.trim().replace(/,/g, ';');
                    rowData.push(`"${text}"`);
                });
                csv.push(rowData.join(','));
            });

            const csvContent = csv.join('\n');
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.setAttribute('download', `tickets_export_${new Date().toISOString().split('T')[0]}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
    }
});