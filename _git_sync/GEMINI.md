# Mandatory Git Workflow (Safety First)

**Local Environment Configuration:**
- **Git Path:** `C:\Program Files\Git\bin\git.exe`
- **Sync Directory:** `D:\hau_erp\_git_sync`

To ensure code integrity and follow the user's preferred version control strategy, the following rules are MANDATORY:

1. **User-Directed Commits:** Perform stage, commit, and push operations ONLY when explicitly requested by the user.
2. **Task Transition Commit:** Before initiating a newly assigned task, ensure any pending changes from the previous task are committed and pushed to the GitHub repository.
3. **Cloud Sync:** Every commit operation must be immediately followed by a 'git push' to 'origin/main'.
4. **Descriptive Messages:** Commit messages must clearly state WHAT was changed and WHY (e.g., "Feature: Integrated new sidebar icons in Employee Portal").
5. **No Force Push:** Force pushing is strictly prohibited unless explicitly instructed by the user.
`n# Engineering Standards`n`n## UI Standards`n`n### Date Picker`n- Use MIT Flatpickr with project-specific light theme.`n- Trigger icon calbtn.gif must be placed immediately to the right of the input.`n`n### Grid Headings`n- Use tablesubheading class with Dark Green background (#2d5a27) and white text.`n`n### Pagination`n- **Mandatory Consistency**: Use the standard sliding-window pagination logic from app/templates/includes/pagination.html.`n- **CSS Class**: Container must use .pager-style.`n- **Active State**: The active page number must use the .active class (typically renders red text in this project).`n- **Multi-Grid Support**: For pages with multiple independent lists, use unique parameters (e.g., page_p, page_h) while preserving the style and logic of the standard pager.
