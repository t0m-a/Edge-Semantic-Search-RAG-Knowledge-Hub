# Git, GitHub & Atom Memo

> [← Back to Main Index](README.md)

## Table of Contents

- [Git Core Workflow](#git-core-workflow)
- [Resetting & Undoing Changes](#resetting--undoing-changes)
- [Initial Configuration & Repository Setup](#initial-configuration--repository-setup)
  - [Global Configuration](#global-configuration)
  - [Create a New Repository from the Command Line](#create-a-new-repository-from-the-command-line)
  - [Push an Existing Repository from the Command Line](#push-an-existing-repository-from-the-command-line)
- [Cleaning Up Directories Locally & in Remote History](#cleaning-up-directories-locally--in-remote-history)
- [Atom Editor Tips](#atom-editor-tips)
- [Useful Git Documentation Links](#useful-git-documentation-links)

---

## Git Core Workflow

The standard order of operations in Git:

1. **Make your changes** in the working directory.
2. **`git add`** — Stages your changes for committing.
3. **`git commit`** — Commits your staged changes to the local repository.
4. **`git push`** — Pushes your committed changes to a remote repository.

> **Key Takeaways:**
> - If you `push` without committing, nothing gets pushed.
> - If you `commit` without adding, nothing gets committed.
> - If you `add` without committing, Git simply records that the staged changes should be included in the next commit.
> - Seeing *"Your branch is ahead of 'origin/master' by 1 commit"* means your local repository has one commit that hasn't been pushed to the remote yet.
> - **`add` and `commit` are local operations**; **`push`, `pull`, and `fetch` interact with a remote**.

---

## Resetting & Undoing Changes

**Hard reset to the previous commit (destructive):**

```bash
git reset --hard HEAD~
```

> **Warning:** Check `git log` first to be sure—`--hard` permanently discards uncommitted local changes.

**Safer alternative using `--soft` and `git stash`:**

```bash
git reset --soft HEAD~   # Reset to the last commit while keeping changes
git stash                # Stash all changes in the working tree
git push                 # Push changes
git stash pop            # Restore your stashed changes
```

Or run `git pull` to synchronize with the remote repository's current state.

---

## Initial Configuration & Repository Setup

Every repository should include a `README.md`, `LICENSE`, and `.gitignore`.

### Global Configuration

Configure Vim as the default editor, enable credential caching, and set your user identity:

```bash
git config --global core.editor "vim"
git config --global credential.helper 'cache --timeout=360000'
git config --global user.name "GithubUserName"
git config --global user.email "AccountEmailAddress"
```

### Create a New Repository from the Command Line

```bash
echo "# REPOSITORY_NAME" >> README.md
git init
git add README.md
git commit -m "first commit"
git remote add origin https://github.com/$USERNAME/$REPO.git
git push -u origin master
```

### Push an Existing Repository from the Command Line

```bash
git remote add origin https://github.com/$USERNAME/$REPO.git
git push -u origin master
```

---

## Cleaning Up Directories Locally & in Remote History

**Remove a tracked directory from the Git index without deleting local files (or commit its removal):**

```bash
git config --global credential.helper 'cache --timeout=3600'
git rm -r --cached REPO_NAME && git commit -m 'Removed old directory "REPO_NAME"' && git push origin master
```

**Purge a directory completely from local and remote commit history (`git filter-branch`):**

From the repository root directory, run:

```bash
git filter-branch -f --tree-filter 'rm -rf package_dir/sub_package_dir' HEAD

# Example:
git filter-branch -f --tree-filter 'rm -rf exercices/exercice-php' HEAD
```

- `-f` forces `filter-branch` to overwrite the backup refs when running multiple filter operations.
- Push the rewritten history to the remote using `--force`:

```bash
git push --force
```

---

## Atom Editor Tips

- **File Treeview Git Status Colors:**
  - **Orange:** Modified file
  - **Green:** New / untracked file
  - **Red:** Deleted file

---

## Useful Git Documentation Links

- [Pro Git Book (EN) — First-Time Git Setup](https://git-scm.com/book/en/v2/Getting-Started-First-Time-Git-Setup)
- [Pro Git Book (FR) — Utilitaires Git : Stockage des identifiants](https://git-scm.com/book/fr/v2/Utilitaires-Git-Stockage-des-identifiants)
