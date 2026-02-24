# Mandatory Git Workflow (Safety First)

To ensure code integrity and follow the user's preferred version control strategy, the following rules are MANDATORY:

1. **User-Directed Commits:** Perform stage, commit, and push operations ONLY when explicitly requested by the user.
2. **Task Transition Commit:** Before initiating a newly assigned task, ensure any pending changes from the previous task are committed and pushed to the GitHub repository.
3. **Cloud Sync:** Every commit operation must be immediately followed by a 'git push' to 'origin/main'.
4. **Descriptive Messages:** Commit messages must clearly state WHAT was changed and WHY (e.g., "Feature: Integrated new sidebar icons in Employee Portal").
5. **No Force Push:** Force pushing is strictly prohibited unless explicitly instructed by the user.
