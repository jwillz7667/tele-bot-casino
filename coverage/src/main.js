import { FilterManager } from './modules/filter.js';
import { SortManager } from './modules/sort.js';
import { ShortcutManager } from './modules/shortcuts.js';

class CoverageReport {
    constructor() {
        // Initialize all managers
        this.filterManager = new FilterManager();
        this.sortManager = new SortManager();
        this.shortcutManager = new ShortcutManager();
    }
}

// Initialize the coverage report when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.coverageReport = new CoverageReport();
}); 