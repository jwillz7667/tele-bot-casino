import { debounce } from '../utils/helpers.js';
import { STORAGE_KEYS, SELECTORS, CLASSES } from '../utils/constants.js';

export class FilterManager {
    constructor() {
        this.filterInput = document.querySelector(SELECTORS.FILTER_INPUT);
        this.hide100Checkbox = document.querySelector(SELECTORS.HIDE100_CHECKBOX);
        this.table = document.querySelector(SELECTORS.INDEX_TABLE);
        this.noRowsMessage = document.querySelector(SELECTORS.NO_ROWS_MESSAGE);
        
        // Virtual scrolling properties
        this.rowHeight = 48; // Default row height in pixels
        this.visibleRows = 20; // Number of rows to render at once
        this.buffer = 10; // Number of rows to buffer above and below
        this.allRows = Array.from(this.table.querySelectorAll('tbody tr'));
        this.virtualScroller = null;
        
        this.setupVirtualScroller();
        this.loadSavedPreferences();
        this.wireUpEvents();
        this.measureRowHeight();
    }

    setupVirtualScroller() {
        // Create virtual scroller container
        const container = document.createElement('div');
        container.className = 'coverage-table-container';
        
        const viewport = document.createElement('div');
        viewport.className = 'coverage-table-viewport';
        
        // Move the table into the virtual scroller
        this.table.parentNode.insertBefore(container, this.table);
        viewport.appendChild(this.table);
        container.appendChild(viewport);
        
        this.virtualScroller = {
            container,
            viewport,
            scrollTop: 0,
            totalHeight: 0,
            visibleRange: { start: 0, end: 0 }
        };

        // Add scroll listener
        container.addEventListener('scroll', debounce(() => {
            this.updateVisibleRows();
        }, 16)); // ~60fps
    }

    measureRowHeight() {
        if (this.allRows.length > 0) {
            const row = this.allRows[0];
            row.style.visibility = 'hidden';
            row.style.display = '';
            this.rowHeight = row.offsetHeight;
            row.style.visibility = '';
        }
    }

    updateVisibleRows() {
        const { container, viewport } = this.virtualScroller;
        const scrollTop = container.scrollTop;
        
        // Calculate visible range
        const startIndex = Math.floor(scrollTop / this.rowHeight) - this.buffer;
        const endIndex = startIndex + this.visibleRows + (this.buffer * 2);
        
        const validStartIndex = Math.max(0, startIndex);
        const validEndIndex = Math.min(this.filteredRows.length - 1, endIndex);
        
        // Update visible range
        this.virtualScroller.visibleRange = {
            start: validStartIndex,
            end: validEndIndex
        };
        
        // Update viewport height and position
        viewport.style.height = `${this.filteredRows.length * this.rowHeight}px`;
        viewport.style.transform = `translateY(${validStartIndex * this.rowHeight}px)`;
        
        // Render visible rows
        this.renderVisibleRows(validStartIndex, validEndIndex);
    }

    renderVisibleRows(startIndex, endIndex) {
        const fragment = document.createDocumentFragment();
        const tbody = this.table.querySelector('tbody');
        
        // Clear current rows
        tbody.innerHTML = '';
        
        // Add visible rows
        for (let i = startIndex; i <= endIndex; i++) {
            if (this.filteredRows[i]) {
                fragment.appendChild(this.filteredRows[i].cloneNode(true));
            }
        }
        
        tbody.appendChild(fragment);
    }

    loadSavedPreferences() {
        const savedFilter = localStorage.getItem(STORAGE_KEYS.FILTER);
        if (savedFilter) {
            this.filterInput.value = savedFilter;
        }

        const savedHide100 = localStorage.getItem(STORAGE_KEYS.HIDE100);
        if (savedHide100) {
            this.hide100Checkbox.checked = JSON.parse(savedHide100);
        }
    }

    wireUpEvents() {
        const filterHandler = debounce(() => this.handleFilter(), 200);
        this.filterInput.addEventListener('input', filterHandler);
        this.hide100Checkbox.addEventListener('input', filterHandler);

        // Add ARIA attributes for accessibility
        this.filterInput.setAttribute('aria-label', 'Filter coverage results');
        this.filterInput.setAttribute('aria-controls', 'coverage-table');
        this.hide100Checkbox.setAttribute('aria-label', 'Hide fully covered files');
    }

    handleFilter() {
        const text = this.filterInput.value;
        const hide100 = this.hide100Checkbox.checked;
        
        // Store preferences
        localStorage.setItem(STORAGE_KEYS.FILTER, text);
        localStorage.setItem(STORAGE_KEYS.HIDE100, JSON.stringify(hide100));

        const casefold = (text === text.toLowerCase());
        
        // Filter rows
        this.filteredRows = this.allRows.filter(row => {
            let show = this.shouldShowRow(row, text, casefold);
            if (show && hide100) {
                show = this.isNotFullyCovered(row);
            }
            return show;
        });

        // Update totals
        const totals = this.calculateTotals();
        
        // Update UI
        this.updateTableVisibility(this.filteredRows.length);
        this.updateTotals(totals);
        
        // Reset virtual scroller
        if (this.virtualScroller) {
            this.virtualScroller.container.scrollTop = 0;
            this.updateVisibleRows();
        }

        // Announce filter results to screen readers
        this.announceFilterResults(this.filteredRows.length);
    }

    calculateTotals() {
        const totals = new Array(this.table.rows[0].cells.length).fill(0);
        totals[totals.length - 1] = { numer: 0, denom: 0 };

        this.filteredRows.forEach(row => {
            this.updateTotalsForRow(row, totals);
        });

        return totals;
    }

    shouldShowRow(row, text, casefold) {
        for (const cell of row.cells) {
            if (cell.classList.contains(CLASSES.NAME_CELL)) {
                let cellText = cell.textContent;
                if (casefold) {
                    cellText = cellText.toLowerCase();
                }
                if (cellText.includes(text)) {
                    return true;
                }
            }
        }
        return false;
    }

    isNotFullyCovered(row) {
        const lastCell = row.cells[row.cells.length - 1];
        const [numer, denom] = lastCell.dataset.ratio.split(' ');
        return numer !== denom;
    }

    updateTotalsForRow(row, totals) {
        totals[0]++;
        
        for (let i = 0; i < totals.length; i++) {
            const cell = row.cells[i];
            if (cell.classList.contains(CLASSES.NAME_CELL)) {
                continue;
            }

            if (i === totals.length - 1) {
                const [numer, denom] = cell.dataset.ratio.split(' ');
                totals[i].numer += parseInt(numer, 10);
                totals[i].denom += parseInt(denom, 10);
            } else {
                totals[i] += parseInt(cell.textContent, 10);
            }
        }
    }

    updateTableVisibility(visibleRowCount) {
        if (!visibleRowCount) {
            this.noRowsMessage.style.display = 'block';
            this.virtualScroller.container.style.display = 'none';
        } else {
            this.noRowsMessage.style.display = 'none';
            this.virtualScroller.container.style.display = '';
        }
    }

    updateTotals(totals) {
        const footer = this.table.tFoot.rows[0];
        
        for (let i = 0; i < totals.length; i++) {
            const cell = footer.cells[i];
            if (cell.classList.contains(CLASSES.NAME_CELL)) {
                continue;
            }

            if (i === totals.length - 1) {
                this.updatePercentageCell(cell, totals[i]);
            } else {
                cell.textContent = totals[i];
            }
        }
    }

    updatePercentageCell(cell, total) {
        const match = /\.([0-9]+)/.exec(cell.textContent);
        const places = match ? match[1].length : 0;
        const { numer, denom } = total;
        
        cell.dataset.ratio = `${numer} ${denom}`;
        cell.textContent = denom
            ? `${(numer * 100 / denom).toFixed(places)}%`
            : `${(100).toFixed(places)}%`;
    }

    announceFilterResults(count) {
        // Create or update live region for screen readers
        let liveRegion = document.getElementById('filter-announcement');
        if (!liveRegion) {
            liveRegion = document.createElement('div');
            liveRegion.id = 'filter-announcement';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.className = 'sr-only';
            document.body.appendChild(liveRegion);
        }
        
        liveRegion.textContent = `${count} files shown`;
    }
} 