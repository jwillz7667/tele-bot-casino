/**
 * Debounces a function call
 * @param {Function} callback - The function to debounce
 * @param {number} wait - The debounce delay in milliseconds
 * @returns {Function} - The debounced function
 */
export function debounce(callback, wait = 300) {
    let timeoutId = null;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
            callback.apply(this, args);
        }, wait);
    };
}

/**
 * Checks if an element is visible in the viewport
 * @param {HTMLElement} element - The element to check
 * @returns {boolean} - Whether the element is visible
 */
export function checkVisible(element) {
    const rect = element.getBoundingClientRect();
    const viewBottom = Math.max(document.documentElement.clientHeight, window.innerHeight);
    const viewTop = 30;
    return !(rect.bottom < viewTop || rect.top >= viewBottom);
}

/**
 * Gets the value of a table cell
 * @param {HTMLTableRowElement} row - The table row
 * @param {number} column - The column index
 * @returns {string|number} - The cell value
 */
export function getCellValue(row, column = 0) {
    const cell = row.cells[column];
    if (cell.childElementCount === 1) {
        let child = cell.firstElementChild;
        if (child.tagName === "A") {
            child = child.firstElementChild;
        }
        if (child instanceof HTMLDataElement && child.value) {
            return child.value;
        }
    }
    return cell.innerText || cell.textContent;
}

/**
 * Compares two table rows for sorting
 * @param {HTMLTableRowElement} rowA - First row
 * @param {HTMLTableRowElement} rowB - Second row
 * @param {number} column - Column index to compare
 * @returns {number} - Comparison result
 */
export function rowComparator(rowA, rowB, column = 0) {
    const valueA = getCellValue(rowA, column);
    const valueB = getCellValue(rowB, column);
    if (!isNaN(valueA) && !isNaN(valueB)) {
        return valueA - valueB;
    }
    return valueA.localeCompare(valueB, undefined, {numeric: true});
} 