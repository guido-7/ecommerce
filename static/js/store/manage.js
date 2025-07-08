document.addEventListener('DOMContentLoaded', function() {
    // Initialize sort arrows based on current sort
    initializeSortArrows();

    // Add click handlers to sortable headers
    document.querySelectorAll('.sortable-header').forEach(header => {
        header.addEventListener('click', function() {
            const sortBy = this.getAttribute('data-sort');
            const isCategory = this.getAttribute('data-table') === 'category';
            handleSort(sortBy, isCategory);
        });
    });

    function initializeSortArrows() {
        // Products table
        const currentSortBy = document.getElementById('sort_by').value;
        const currentSortOrder = document.getElementById('sort_order').value;

        if (currentSortBy) {
            updateSortArrows(currentSortBy, currentSortOrder, false);
        }

        // Categories table
        const currentCategorySortBy = document.getElementById('category_sort_by').value;
        const currentCategorySortOrder = document.getElementById('category_sort_order').value;

        if (currentCategorySortBy) {
            updateSortArrows(currentCategorySortBy, currentCategorySortOrder, true);
        }
    }

    function updateSortArrows(sortBy, sortOrder, isCategory) {
        // Clear all active arrows
        const tableSelector = isCategory ? '[data-table="category"]' : ':not([data-table="category"])';
        document.querySelectorAll(`.sortable-header${tableSelector} .sort-arrow`).forEach(arrow => {
            arrow.classList.remove('active');
        });

        // Activate the correct arrow
        const activeHeader = document.querySelector(`.sortable-header[data-sort="${sortBy}"]${tableSelector}`);
        if (activeHeader) {
            const activeArrow = activeHeader.querySelector(`.sort-arrow[data-direction="${sortOrder}"]`);
            if (activeArrow) {
                activeArrow.classList.add('active');
            }
        }
    }

    function handleSort(sortBy, isCategory = false) {
        if (isCategory) {
            const currentSortBy = document.getElementById('category_sort_by').value;
            const currentSortOrder = document.getElementById('category_sort_order').value;

             let newSortOrder = 'asc';
            if (currentSortBy === sortBy && currentSortOrder === 'asc') {
                newSortOrder = 'desc';
            }

            document.getElementById('category_sort_by').value = sortBy;
            document.getElementById('category_sort_order').value = newSortOrder;

            // Activate categories tab and submit form
            //document.getElementById('categories-tab').click();
            //setTimeout(() => {
            //document.getElementById('categoryFilterForm').submit();
            //}, 100);

            document.getElementById('categoryFilterForm').submit();
        } else {
            const currentSortBy = document.getElementById('sort_by').value;
            const currentSortOrder = document.getElementById('sort_order').value;

            let newSortOrder = 'asc';
            if (currentSortBy === sortBy && currentSortOrder === 'asc') {
                newSortOrder = 'desc';
            }

            document.getElementById('sort_by').value = sortBy;
            document.getElementById('sort_order').value = newSortOrder;

            document.getElementById('filterForm').submit();
        }
    }
});