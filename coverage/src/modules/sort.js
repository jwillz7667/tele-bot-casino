import { rowComparator } from '../utils/helpers.js';
import { STORAGE_KEYS } from '../utils/constants.js';

export class SortManager {
    constructor() {
        this.initializeSortHandlers();
        this.restoreSortState();
    }

    initializeSortHandlers() {
        document.querySelectorAll('th[aria-sort]').forEach(th => {
            th.addEventListener('click', () => this.sortColumn(th));
        });
    }

    restoreSortState() {
        const storedSort = localStorage.getItem(STORAGE_KEYS.INDEX_SORT);
        if (storedSort) {
            const { th_id, direction } = JSON.parse(storedSort);
            const th = document.getElementById(th_id);
            if (th) {
                this.sortColumn(th, direction);
            }
        }

        const storedRegionSort = localStorage.getItem(STORAGE_KEYS.SORTED_BY_REGION);
        if (storedRegionSort) {
            const { by_region, region_direction } = JSON.parse(storedRegionSort);
            const regionTh = document.getElementById('region');
            if (by_region && regionTh) {
                this.sortColumn(regionTh, region_direction);
            }
        }
    }

    sortColumn(th, forcedDirection = null) {
        // Get or determine sort direction
        const currentSortOrder = th.getAttribute('aria-sort');
        let direction = forcedDirection;
        
        if (!direction) {
            if (currentSortOrder === 'none') {
                direction = th.dataset.defaultSortOrder || 'ascending';
            } else if (currentSortOrder === 'ascending') {
                direction = 'descending';
            } else {
                direction = 'ascending';
            }
        }

        // Clear all sort indicators
        th.parentElement.querySelectorAll('th').forEach(header => {
            header.setAttribute('aria-sort', 'none');
        });

        // Set new sort direction
        th.setAttribute('aria-sort', direction);

        // Get column index
        const column = Array.from(th.parentElement.children).indexOf(th);

        // Sort the table
        const tbody = th.closest('table').querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        rows.sort((rowA, rowB) => 
            rowComparator(rowA, rowB, column) * (direction === 'ascending' ? 1 : -1)
        );

        // Reorder rows in the DOM
        rows.forEach(row => tbody.appendChild(row));

        // Save sort state
        this.saveSortState(th, direction);
    }

    saveSortState(th, direction) {
        if (th.id !== 'region') {
            localStorage.setItem(STORAGE_KEYS.INDEX_SORT, JSON.stringify({
                th_id: th.id,
                direction: direction
            }));

            // If sorting by non-region column, clear region sort state
            if (th.id !== document.getElementById('region')?.id) {
                localStorage.setItem(STORAGE_KEYS.SORTED_BY_REGION, JSON.stringify({
                    by_region: false,
                    region_direction: direction
                }));
            }
        } else {
            // Save region sort state
            localStorage.setItem(STORAGE_KEYS.SORTED_BY_REGION, JSON.stringify({
                by_region: true,
                region_direction: direction
            }));
        }
    }
} 