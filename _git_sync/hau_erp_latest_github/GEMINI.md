
# Mandatory Git Workflow (Safety First)

**Local Environment Configuration:**
- **Git Path:** `C:\Program Files\Git\bin\git.exe`

To prevent code loss and ensure complete version control, the following rules are MANDATORY for all operations:

1. **Pre-Task Save:** Before making any modifications to the codebase, check for uncommitted changes. If they exist, commit them with the message: "Pre-task save: [Brief description of pending work]".
2. **Surgical Commits:** After completing a specific task or edit, immediately stage and commit the changes.
3. **Descriptive Messages:** Every commit message must clearly state WHAT was changed and WHY (e.g., "Fix: Resolved null pointer in Employee Master login").
4. **Cloud Sync:** After every commit, perform a 'git push' to ensure the GitHub repository (origin/main) is synchronized.
5. **No Force Push:** Never use force push unless explicitly directed by the user.

