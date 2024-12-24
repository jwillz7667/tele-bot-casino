import { SELECTORS } from '../utils/constants.js';

export class ShortcutManager {
    constructor() {
        this.assignShortcuts();
    }

    assignShortcuts() {
        const shortcutElements = document.querySelectorAll(SELECTORS.SHORTCUT_ELEMENTS);
        
        shortcutElements.forEach(element => {
            document.addEventListener('keypress', event => {
                // Ignore keypress when focus is in an input field
                if (event.target.tagName.toLowerCase() === 'input') {
                    return;
                }
                
                if (event.key === element.dataset.shortcut) {
                    element.click();
                }
            });
        });
    }
} 